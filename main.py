
import os
import datetime as dt
from dotenv import load_dotenv
from agent_core.orchestrator import PlannerOrchestrator
from agent_core.conversational_planner import ConversationalPlanner
from tools.google_calendar import CalendarManager

def main():
    load_dotenv(dotenv_path=os.path.join('config', '.env'))
    API_KEY = os.getenv("GOOGLE_API_KEY")
    if not API_KEY:
        raise ValueError("A chave de API do Google não foi encontrada.")

    INPUT_FOLDER = "input_proofs"
    OUTPUT_FOLDER = "output_topics"
    os.makedirs(INPUT_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    print("="*50)
    print("🤖 INICIANDO AGENTE ORGANIZADOR DE ESTUDOS 🤖")
    print("="*50)

    # --- FASE 1: Análise de Conteúdo e Agenda ---
    orchestrator = PlannerOrchestrator(api_key=API_KEY)
    topics_summary = orchestrator.analyze_and_generate_pdfs(INPUT_FOLDER, OUTPUT_FOLDER)
    
    if "❌" in topics_summary:
        print(topics_summary)
        return

    calendar_manager = CalendarManager()
    schedule_summary = calendar_manager.analyze_schedule_for_llm(dt.date.today())

    # --- FASE 2: Conversa com o Agente de Planejamento ---
    planner_agent = ConversationalPlanner(api_key=API_KEY)
    planner_agent.start_conversation(topics_summary, schedule_summary)

    while True:
        user_input = input("\n--- Você ---\n")
        
        if user_input.lower() in ['sair', 'exit', 'quit']:
            print("Até mais!")
            break
            
        planner_agent.chat(user_input)
        
        final_preferences = planner_agent.is_plan_finalized()
        
        if final_preferences:
            # Verifica se a data de início existe e, se não, usa a data de hoje como padrão.
            if not final_preferences.get('start_date'):
                today_str = dt.date.today().strftime('%Y-%m-%d')
                print(f"⚠️ Data de início não foi especificada na conversa. Usando a data de hoje: {today_str}")
                final_preferences['start_date'] = today_str
            # --------------------------------

            print("\n✅ Ótimo! Entendi que o plano está pronto. Preparando para agendar...")
            try:
                orchestrator.schedule_with_preferences(final_preferences)
                break
            except Exception as e:
                print(f"Houve um problema ao tentar agendar: {e}")
                print("Vamos tentar refinar os detalhes.")


if __name__ == '__main__':
    main()