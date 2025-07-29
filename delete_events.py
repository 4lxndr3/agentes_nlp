import os
import datetime as dt
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from tqdm import tqdm

# Configurações
SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_FILE = 'config/credentials.json'
TOKEN_FILE = 'config/token.json'

def authenticate():
    """
    Realiza a autenticação interativa do usuário, reutilizando o token se existir.
    """
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    
    return build('calendar', 'v3', credentials=creds)

def main():
    """
    Script para encontrar e deletar eventos criados pelo 'study_planner_agent'.
    """
    print("--- Script de Limpeza de Eventos do Google Calendar (Modo credentials.json) ---")

    try:
        service = authenticate()
    except Exception as e:
        print(f"❌ Erro de autenticação: {e}")
        print("Verifique se o arquivo 'config/credentials.json' está correto e se o fluxo de autorização no navegador foi concluído.")
        return

    # Coleta o intervalo de datas do usuário
    start_date_str = input("Digite a data de INÍCIO para a busca (AAAA-MM-DD): ")
    end_date_str = input("Digite a data de FIM para a busca (AAAA-MM-DD): ")

    try:
        time_min = dt.datetime.strptime(start_date_str, '%Y-%m-%d').isoformat() + 'Z'
        time_max = dt.datetime.strptime(end_date_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59).isoformat() + 'Z'
    except ValueError:
        print("❌ Formato de data inválido. Use AAAA-MM-DD.")
        return

    print(f"\nBuscando eventos entre {start_date_str} e {end_date_str}...")

    # --- Busca por Eventos ---
    events_result_tagged = service.events().list(
        calendarId='primary', timeMin=time_min, timeMax=time_max,
        privateExtendedProperty='creator=study_planner_agent_v1',
        singleEvents=True, orderBy='startTime'
    ).execute()
    events_tagged = events_result_tagged.get('items', [])

    events_to_delete = list(events_tagged)
    print("Buscando eventos antigos (sem etiqueta) pelo título...")
    events_result_untagged = service.events().list(
        calendarId='primary', timeMin=time_min, timeMax=time_max,
        q='Estudar:', singleEvents=True, orderBy='startTime'
    ).execute()
    events_untagged = events_result_untagged.get('items', [])

    existing_ids = {event['id'] for event in events_to_delete}
    for event in events_untagged:
        if 'extendedProperties' not in event and event['id'] not in existing_ids:
            if event['summary'].startswith("Estudar:"):
                 events_to_delete.append(event)


    if not events_to_delete:
        print("\nNenhum evento criado pelo sistema foi encontrado no período especificado.")
        return

    # --- Confirmação do Usuário ---
    print(f"\nEncontrei {len(events_to_delete)} evento(s) para apagar:")
    for event in events_to_delete:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(f"  - {start.split('T')[0]}: {event['summary']}")

    confirm = input("\nVocê tem certeza que deseja apagar permanentemente esses eventos? (s/n): ").lower()

    if confirm != 's':
        print("Operação cancelada.")
        return

    # --- Deleção dos Eventos ---
    print("\nApagando eventos...")
    for event in tqdm(events_to_delete, desc="Deletando"):
        try:
            service.events().delete(calendarId='primary', eventId=event['id']).execute()
        except Exception as e:
            print(f"Não foi possível apagar o evento '{event['summary']}': {e}")
    
    print("\n✅ Limpeza concluída com sucesso!")

if __name__ == '__main__':
    main()