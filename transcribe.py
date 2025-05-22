import sys
sys.stdout.reconfigure(encoding='utf-8')
audio_file = sys.argv[1]
import os
import whisper
import ffmpeg as ff
import requests

if len(sys.argv) < 2:
    print("❌ Caminho do arquivo de áudio não fornecido.")
    exit(1)

input_path = os.path.abspath(sys.argv[1])
if not os.path.exists(input_path):
    print(f"❌ Arquivo não encontrado: {input_path}")
    exit(1)

TEMP_MP3 = "temp.mp3"

print(f"\n📂 Arquivo detectado: {os.path.basename(input_path)}")
print(f"📍 Caminho absoluto: {input_path}")
print("🔄 Convertendo para MP3 via ffmpeg-python...")

try:
    (
        ff
        .input(input_path)
        .output(TEMP_MP3, format='mp3')
        .run(overwrite_output=True, quiet=True)
    )
    print("✅ Conversão concluída.")
except Exception as e:
    print(f"❌ Erro durante conversão com ffmpeg-python:\n{e}")
    exit(1)

print("🎙️ Iniciando transcrição com Whisper...")
try:
    model = whisper.load_model("small")
    result = model.transcribe(TEMP_MP3, language='pt')
    transcribed_text = result['text']
    print("📄 Transcrição:")
    print(transcribed_text)

    print("📡 Enviando transcrição para análise...")
    response = requests.post("http://localhost:8000/analyze-text", json={"message": transcribed_text})
    if response.status_code == 200:
        analysis = response.json()
        print("\n🧠 Resultado da IA:")
        print(f"🔍 Risco: {analysis['risk']}")
        print(f"💬 Motivo: {analysis['reason']}")
        print(f"📊 Confiança: {analysis['confidence']}")
    else:
        print(f"⚠️ Erro ao analisar transcrição. Status: {response.status_code}")
except Exception as e:
    print(f"❌ Erro na transcrição ou análise:\n{e}")

# 🧹 Limpa arquivo temporário
if os.path.exists(TEMP_MP3):
    os.remove(TEMP_MP3)
