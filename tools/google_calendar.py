import os.path
import datetime as dt
from time import sleep
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from collections import Counter

SCOPES = ['https://www.googleapis.com/auth/calendar']

class CalendarManager:
    def __init__(self, credentials_path='config/credentials.json', token_path='config/token.json'):
        creds = None
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('calendar', 'v3', credentials=creds)

    def analyze_schedule_for_llm(self, start_date: dt.date, num_days: int = 14) -> str:
        """
        Analisa a agenda e gera um resumo em texto para ser usado por um LLM.
        """
        print("\n🤖 Analisando sua agenda para entender seus padrões de horários...")
        time_min = dt.datetime.combine(start_date, dt.time.min).isoformat() + 'Z'
        time_max = dt.datetime.combine(start_date + dt.timedelta(days=num_days), dt.time.max).isoformat() + 'Z'

        try:
            events_result = self.service.events().list(
                calendarId='primary', timeMin=time_min, timeMax=time_max,
                singleEvents=True, orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])
        except Exception as e:
            return f"Não foi possível acessar a agenda: {e}. Não há dados de horários."

        if not events:
            return "Sua agenda parece estar completamente livre nos próximos 14 dias. Todos os horários são boas sugestões."

        busy_periods = Counter()
        day_names = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]

        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            start_dt = dt.datetime.fromisoformat(start.replace('Z', '+00:00')).astimezone()
            
            day_of_week = day_names[start_dt.weekday()]
            hour = start_dt.hour

            if 6 <= hour < 12:
                period = "Manhã"
            elif 12 <= hour < 18:
                period = "Tarde"
            else:
                period = "Noite"
            
            busy_periods[f"{day_of_week} de {period}"] += 1
        
        # Gera um resumo textual
        summary = "Resumo dos seus compromissos na agenda para os próximos 14 dias:\n"
        for period, count in busy_periods.most_common():
            summary += f"- O período de '{period}' parece ser o mais ocupado (com {count} evento(s)).\n"
        
        return summary
    def find_free_time_slots(self, start_date: dt.date, num_days: int = 7):
        print("\n🤖 Analisando sua agenda para encontrar os melhores horários...")
        time_min = dt.datetime.combine(start_date, dt.time.min).isoformat() + 'Z'
        time_max = dt.datetime.combine(start_date + dt.timedelta(days=num_days), dt.time.max).isoformat() + 'Z'
        body = {"timeMin": time_min, "timeMax": time_max, "items": [{"id": "primary"}]}
        try:
            free_busy_result = self.service.freebusy().query(body=body).execute()
            busy_slots = free_busy_result['calendars']['primary']['busy']
        except Exception as e:
            print(f"⚠️ Não foi possível analisar a agenda: {e}. Usando horários padrão.")
            return {'Manhã': '09:00', 'Tarde': '14:00', 'Noite': '19:00'}
        study_blocks = {'Manhã': {'start': 9, 'end': 12, 'suggestion': '09:00'},'Tarde': {'start': 14, 'end': 17, 'suggestion': '14:00'},'Noite': {'start': 19, 'end': 22, 'suggestion': '19:00'}}
        free_slots_count = {'Manhã': 0, 'Tarde': 0, 'Noite': 0}
        for day_offset in range(num_days):
            current_day = start_date + dt.timedelta(days=day_offset)
            for block_name, block_times in study_blocks.items():
                is_block_free = True
                block_start = dt.datetime.combine(current_day, dt.time(hour=block_times['start']))
                block_end = dt.datetime.combine(current_day, dt.time(hour=block_times['end']))
                for busy in busy_slots:
                    busy_start = dt.datetime.fromisoformat(busy['start'].replace('Z', '+00:00')).astimezone().replace(tzinfo=None)
                    busy_end = dt.datetime.fromisoformat(busy['end'].replace('Z', '+00:00')).astimezone().replace(tzinfo=None)
                    if max(block_start, busy_start) < min(block_end, busy_end):
                        is_block_free = False
                        break
                if is_block_free:
                    free_slots_count[block_name] += 1
        suggestions = {}
        for block_name, count in free_slots_count.items():
            if count > num_days / 2:
                suggestions[block_name] = study_blocks[block_name]['suggestion']
        return suggestions if suggestions else {'Manhã': '09:00', 'Tarde': '14:00'}

    def create_study_event(self, summary: str, description: str, start_datetime: dt.datetime):
        end_datetime = start_datetime + dt.timedelta(hours=1)
        event = {
            'summary': summary,
            'description': description,
            'start': {'dateTime': start_datetime.isoformat(), 'timeZone': 'America/Manaus'},
            'end': {'dateTime': end_datetime.isoformat(), 'timeZone': 'America/Manaus'},
            'reminders': {'useDefault': False, 'overrides': [{'method': 'popup', 'minutes': 30}]},
            'extendedProperties': {'private': {'creator': 'study_planner_agent_v1'}}
        }
        try:
            self.service.events().insert(calendarId='primary', body=event).execute()
        except Exception as e:
            print(f"⚠️ Erro ao tentar criar evento '{summary}': {e}")

    def verify_events_creation(self, expected_events: list):
        """
        Verifica se uma lista de eventos esperados foi realmente criada na agenda.
        """
        if not expected_events:
            return

        print("\n🔍 Verificando se todos os eventos foram salvos corretamente...")
        sleep(30)

        # Define o intervalo de tempo para a busca
        min_date = min(evt['start_datetime'] for evt in expected_events)
        max_date = max(evt['start_datetime'] for evt in expected_events)
        time_min = min_date.isoformat() + 'Z'
        time_max = (max_date + dt.timedelta(days=1)).isoformat() + 'Z'

        # Busca todos os eventos criados pelo agente nesse período
        try:
            results = self.service.events().list(
                calendarId='primary', timeMin=time_min, timeMax=time_max,
                privateExtendedProperty='creator=study_planner_agent_v1',
                singleEvents=True
            ).execute()
            actual_events = results.get('items', [])
        except Exception as e:
            print(f"⚠️ Não foi possível verificar os eventos: {e}")
            return

        # Cria um conjunto de eventos encontrados para busca rápida
        found_events_set = set()
        for event in actual_events:
            start_str = event['start'].get('dateTime', '').split('.')[0]
            start_dt = dt.datetime.fromisoformat(start_str)
            found_events_set.add((event['summary'], start_dt))

        # Compara a lista esperada com a lista encontrada
        successful_events = []
        failed_events = []
        for expected in expected_events:
            if (expected['summary'], expected['start_datetime']) in found_events_set:
                successful_events.append(expected)
            else:
                failed_events.append(expected)

        # Apresenta o resultado da verificação
        print("-" * 50)
        if successful_events:
            print(f"✅ Verificação concluída: {len(successful_events)} de {len(expected_events)} eventos foram salvos com sucesso!")
        
        if failed_events:
            print(f"❌ Atenção: {len(failed_events)} eventos não puderam ser confirmados na sua agenda:")
            for failed in failed_events:
                print(f"  - Tópico: {failed['summary']}")
                print(f"    Data e Hora: {failed['start_datetime'].strftime('%Y-%m-%d às %H:%M')}")
        print("-" * 50)