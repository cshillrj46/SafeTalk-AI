// whatsapp-web.js
const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios = require('axios');
const fs = require('fs');
const path = require('path');
const mime = require('mime-types');
const express = require('express');
const { exec } = require('child_process');

console.log("⚙️ Inicializando bot antifraude...");

// 📁 Pasta de áudios
const audioDir = path.resolve(__dirname, 'audios');
if (!fs.existsSync(audioDir)) {
    fs.mkdirSync(audioDir, { recursive: true });
    console.log("📁 Pasta 'audios' criada com sucesso.");
}

// 🤖 Inicializa cliente WhatsApp com autenticação local
const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        headless: false,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    }
});

let BOT_NUMBER = "";

client.on('loading_screen', (percent, message) => {
    console.log(`⏳ Carregando WhatsApp... (${percent}%) ${message}`);
});

client.on('authenticated', () => {
    console.log("🔑 Autenticado com sucesso.");
});

client.on('auth_failure', (msg) => {
    console.error("❌ Falha na autenticação:", msg);
});

client.on('disconnected', (reason) => {
    console.warn("⚠️ Desconectado do WhatsApp. Motivo:", reason);
});

client.on('qr', qr => {
    qrcode.generate(qr, { small: true });
    console.log("📲 Escaneie o QR code com seu WhatsApp para conectar.");
});

client.on('ready', async () => {
    BOT_NUMBER = client.info.wid._serialized;
    console.log("✅ Bot conectado ao WhatsApp!");
    console.log("🤖 Meu número é:", BOT_NUMBER);
    await client.sendMessage(BOT_NUMBER, "🤖 Bot antifraude iniciado com sucesso!");
});

client.on('message', async (msg) => {
    if (msg.fromMe) return;

    const recipient = msg.to || msg.from;

    console.log("📩 Nova mensagem recebida:");
    console.log("- De:", msg.from);
    console.log("- Para:", msg.to);
    console.log("- Conteúdo:", msg.body || '[mídia]');
    console.log("- Tipo:", msg.type);

    // 🔧 Comando de teste
    if (msg.body?.toLowerCase() === "!teste") {
        await client.sendMessage(recipient, "✅ Bot ativo e funcionando.");
        return;
    }

    // 🎧 Mídia de áudio
    if (msg.hasMedia) {
        try {
            const media = await msg.downloadMedia();
            if (media && media.mimetype?.startsWith('audio')) {
                const extension = mime.extension(media.mimetype) || "ogg";
                const filename = `audio_${Date.now()}.${extension}`;
                const filepath = path.join(audioDir, filename);

                fs.writeFileSync(filepath, Buffer.from(media.data, 'base64'));
                console.log(`🎧 Áudio salvo: ${filename}`);

                // 🧠 Executa o transcribe.py com o caminho completo
                const transcribePath = path.resolve(__dirname, '../transcribe.py');
                const command = `python "${transcribePath}" "${filepath}"`;

                console.log("🎙️ Iniciando transcrição com Whisper...");
                exec(command, (error, stdout, stderr) => {
                    if (error) {
                        console.error("❌ Erro ao executar transcribe.py:", error.message);
                        if (stderr.includes("não é áudio") || stderr.includes("not compatible")) {
                            console.warn("⚠️ Mídia recebida não era um áudio válido. Ignorada.");
                        } else {
                            console.error("📛 STDERR:", stderr);
                        }
                        return;
                    }

                    if (stdout.includes("Transcrição:")) {
                        console.log(stdout);
                    } else {
                        console.warn("⚠️ transcribe.py executou, mas não retornou transcrição.");
                    }
                });

            } else {
                console.log("ℹ️ Mídia recebida não é áudio compatível. Ignorada.");
            }
        } catch (err) {
            console.error("❌ Erro ao processar mídia:", err.message);
        }
        return;
    }

    // ✉️ Texto comum
    try {
        const { data } = await axios.post('http://localhost:8000/analyze-text', {
            message: msg.body
        });

        console.log("🧠 Resultado IA:", data);

        if (data.risk && data.risk.includes("golpe")) {
            const alerta = `⚠️ ALERTA DE GOLPE DETECTADO\n\n📩 Mensagem: "${msg.body}"\n🧠 Motivo: ${data.reason}\n📊 Confiança: ${data.confidence}`;
            await client.sendMessage(recipient, alerta);
            console.log("✅ Alerta enviado para:", recipient);
        }
    } catch (error) {
        console.error("❌ Erro na análise IA:", error.message);
    }
});

client.initialize();

// 🌐 Servidor para alertas externos
const app = express();
app.use(express.json());

app.post('/alert', (req, res) => {
    const { number, message } = req.body;

    if (number && message) {
        client.sendMessage(number, message);
        console.log(`🚨 Alerta externo enviado para ${number}: ${message}`);
        res.send({ status: 'Alert sent to recipient.' });
    } else {
        res.status(400).send({ error: 'Missing number or message.' });
    }
});

app.listen(3000, () => {
    console.log("🧭 Servidor Express ouvindo em http://localhost:3000/alert");
});
