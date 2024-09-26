import openai
import requests
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# Defina sua chave de API do OpenAI
openai.api_key = ''

# Configura o driver do Chrome
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# Abre a página da prova
driver.get('https://learn.corporate.ef.com/study/leveltest?testid=20000526')

def obter_resposta_chatgpt(pergunta, opcoes):
    prompt = f"Pergunta: {pergunta}\nOpções:\n" + "\n".join([f"- {opcao}" for opcao in opcoes]) + "\nResponda apenas com o nome da opção correta."
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você é um assistente útil."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message['content'].strip().lstrip('-').strip()
    except Exception as e:
        print(f"Erro ao consultar o ChatGPT: {e}")
        return None

def clicar_botao_next():
    try:
        next_button = driver.find_element(By.CSS_SELECTOR, 'button.c-button.-primary[data-qa="next_btn"]')
        next_button.click()
        print("Botão 'Next' clicado.")
        time.sleep(5)
    except Exception as e:
        print(f"Erro ao clicar no botão 'Next': {e}")

def abrir_ebook():
    try:
        ebook_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.c-link[data-qa='reading-modal']"))
        )
        ebook_link.click()
        print("E-book aberto.")
        time.sleep(5)
    except Exception as e:
        print(f"Erro ao abrir o E-book: {e}")

def responder_pergunta():
    try:
        if driver.find_elements(By.CSS_SELECTOR, "a.c-link[data-qa='reading-modal']"):
            abrir_ebook()
        
        pergunta_element = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".c-questions__question[data-qa='question-question']"))
        )
        pergunta_texto = pergunta_element.text
        print(f"Pergunta: {pergunta_texto}")
        
        opcoes = driver.find_elements(By.CSS_SELECTOR, ".c-questions__answers li")
        opcoes_textos = [opcao.find_element(By.CSS_SELECTOR, ".c-boolean__label").text for opcao in opcoes]
        print(f"Opções: {opcoes_textos}")
        
        resposta_correta = obter_resposta_chatgpt(pergunta_texto, opcoes_textos)
        if resposta_correta:
            print(f"Resposta correta: {resposta_correta}")
            opcao_encontrada = False
            for opcao in opcoes:
                label_texto = opcao.find_element(By.CSS_SELECTOR, ".c-boolean__label").text.strip()
                if label_texto == resposta_correta.strip():
                    opcao.click()  # Seleciona a opção correta
                    opcao_encontrada = True
                    print(f"Opção '{label_texto}' selecionada.")
                    break

            if opcao_encontrada:
                time.sleep(3)  # Aguarda antes de clicar no próximo
                clicar_botao_next()
            else:
                print("Resposta não encontrada entre as opções.")
    
    except Exception as e:
        print(f"Erro ao responder a pergunta: {e}")
        print("HTML da página atual:")
        print(driver.page_source)

def avancar_para_proxima_secao():
    try:
        print("Verificando se o modal está presente...")
        modal = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".c-lt-modal"))
        )
        if modal:
            print("Modal encontrado.")
            modal_texto = modal.find_element(By.CSS_SELECTOR, ".c-lt-modal__title").text
            print(f"Modal: {modal_texto}")
            
            continuar_button = modal.find_element(By.XPATH, "//button//span[text()='Continue to next section']")
            continuar_button.click()
            
            time.sleep(2)
        else:
            print("Modal não encontrado.")
    
    except Exception as e:
        print(f"Erro ao avançar para a próxima seção: {e}")

def processar_audio(audio_url):
    if not audio_url:
        print("URL do áudio não encontrada.")
        return None

    response = requests.get(audio_url)
    
    with open('audio.mp3', 'wb') as f:
        f.write(response.content)
    
    try:
        audio_file = open("audio.mp3", "rb")
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
        return transcript['text']
    
    except Exception as e:
        print(f"Erro ao transcrever o áudio: {e}")
        return None

# Cache para armazenar transcrições de áudios já processados
transcricoes_audios = {}

def responder_secao_com_audio(audio_urls):
    resposta_correta = None

    for audio_url in audio_urls:
        if audio_url in transcricoes_audios:
            print(f"Usando transcrição armazenada para o áudio: {audio_url}")
            transcricao_audio = transcricoes_audios[audio_url]
        else:
            print(f"Processando novo áudio: {audio_url}")
            transcricao_audio = processar_audio(audio_url)
            if transcricao_audio:
                transcricoes_audios[audio_url] = transcricao_audio  # Armazena a transcrição para uso futuro

        if transcricao_audio:
            print(f"Transcrição do áudio: {transcricao_audio}")
            
            pergunta_element = driver.find_element(By.CSS_SELECTOR, ".c-questions__question[data-qa='question-question']")
            pergunta_texto = pergunta_element.text
            opcoes = driver.find_elements(By.CSS_SELECTOR, ".c-questions__answers li")
            opcoes_textos = [opcao.find_element(By.CSS_SELECTOR, ".c-boolean__label").text for opcao in opcoes]
            
            resposta_correta = obter_resposta_chatgpt(f"Transcrição do áudio: {transcricao_audio}\nPergunta: {pergunta_texto}", opcoes_textos)
            if resposta_correta:
                print(f"Resposta correta: {resposta_correta}")
                opcao_encontrada = False
                for opcao in opcoes:
                    label_texto = opcao.find_element(By.CSS_SELECTOR, ".c-boolean__label").text.strip()
                    if label_texto == resposta_correta.strip():
                        opcao.click()  # Seleciona a opção correta
                        opcao_encontrada = True
                        print(f"Opção '{label_texto}' selecionada.")
                        break
                
                if opcao_encontrada:
                    clicar_botao_next()
                    break  # Sai do loop ao encontrar a resposta correta
                else:
                    print("Resposta não encontrada entre as opções.")
            
            else:
                print("Não foi possível obter uma resposta do ChatGPT para a seção de áudio.")
        
        else:
            print(f"Não foi possível transcrever o áudio de URL: {audio_url}")

    if not resposta_correta:
        print("Nenhuma resposta correta foi encontrada após processar todos os áudios.")
    
    time.sleep(2)

# URLs dos áudios
audio_urls = [
    "https://et2.ef-cdn.com/Juno/12/18/86/v/121886/GE_4.7.1.4.2_v2.mp3", 
    "https://et2.ef-cdn.com/Juno/12/18/84/v/121884/GE_4.7.1.4.3_v2.mp3"
]

# Loop para percorrer todas as perguntas e seções
while True:
    try:
        if driver.find_elements(By.CSS_SELECTOR, ".c-audio"):
            responder_secao_com_audio(audio_urls)
        else:
            responder_pergunta()
        
        try:
            print("Verificando se há um modal para avançar...")
            modal = driver.find_element(By.CSS_SELECTOR, ".c-lt-modal")
            if modal:
                avancar_para_proxima_secao()
        except:
            pass
        
    except Exception as e:
        print(f"Erro no loop principal: {e}")
        break
      
