import os
import io
import contextlib
from fastapi import FastAPI, Request
from nicegui import ui, run
import uvicorn
# Import your real logic functions
from app.tests import run_all_tests
from app.tests import db_test
from app.tests import parser_test
# Assume your search services are here
# from app.services.search import perform_search 

fastapi_app = FastAPI()

# --- UI Logic ---

class State:
    search_mode = 'Personal Data'
    test_output = ""
    has_results = False  # Add this flag

state = State()

@ui.page('/')
def main_page():
    ui.colors(primary='#2e59ff', secondary='#4e73df', accent='#1cc88a')
    
    with ui.header().classes('items-center justify-between bg-slate-800'):
        ui.label('CV RAG: Senior Search Lab').classes('text-white font-bold text-lg')
        ui.button('API Docs', on_click=lambda: ui.open('/docs')).props('flat color=white')

    with ui.row().classes('w-full no-wrap h-screen'):
        
        # --- LEFT DRAWER: Search & Filters ---
        with ui.column().classes('w-1/3 p-6 bg-slate-50 border-r'):
            ui.label('Search Configuration').classes('text-xl font-bold mb-4')
            
            # 3) Radio buttons for search mode
            mode_radio = ui.radio(['Personal Data', 'Project Data', 'Aggregate Both'], 
                                  value=state.search_mode).bind_value(state, 'search_mode')
            
            ui.separator().classes('my-4')

            # 1) Search Query Input
            query_input = ui.textarea('Search Query').classes('w-full shadow-sm bg-white').props('outlined')

            # 4) Contextual Filters
            ui.label('Filters').classes('font-bold mt-4')
            
            # Container for dynamic filters
            with ui.column().classes('w-full'):
                # Language & Level (Personal/Aggregate)
                with ui.column().bind_visibility_from(state, 'search_mode', 
                    backward=lambda m: m in ['Personal Data', 'Aggregate Both']):
                    ui.select(['English B2', 'Japanese N2', 'German C1'], label='Languages', multiple=True).classes('w-full')
                    ui.select(['junior', 'mid', 'senior'], label='Candidate Level', multiple=True).classes('w-full')
                
                # Project Roles (Project/Aggregate)
                with ui.column().bind_visibility_from(state, 'search_mode', 
                    backward=lambda m: m in ['Project Data', 'Aggregate Both']):
                    ui.select(['ML Engineer', 'Data Scientist', 'Project Manager'], label='Project Roles', multiple=True).classes('w-full')

            ui.button('EXECUTE SEARCH', on_click=lambda: ui.notify("Retriever Logic Required")).classes('w-full mt-6 h-12 text-lg')

        # --- RIGHT COLUMN: Results & Testing Dashboard ---
        with ui.column().classes('w-2/3 p-6 gap-6'):
            
            # 2) Results Output f
            # with ui.expansion('Search Results', icon='search', value=True).classes('w-full bg-white border'):
            #     results_container = ui.column().classes('w-full p-4')
            #     ui.label('No search performed yet.').classes('text-gray-400').bind_visibility_from(results_container, 'inner_html', backward=lambda x: not x)
            with ui.expansion('Search Results', icon='search', value=True).classes('w-full bg-white border'):
                results_container = ui.column().classes('w-full p-4')
                
                # Bind visibility to our new state flag
                ui.label('No search performed yet.') \
                    .classes('text-gray-400') \
                    .bind_visibility_from(state, 'has_results', backward=lambda x: not x)            
            
            
            # 5) Testing Dashboard
            ui.separator()
            ui.label('Testing Dashboard').classes('text-xl font-bold')
            
            with ui.row().classes('w-full gap-2'):
                async def run_test_logic(func, name):
                    ui.notify(f'Running {name}...')
                    output = io.StringIO()
                    with contextlib.redirect_stdout(output):
                        await run.io_bound(func, verbose=True)
                    test_log.push(f"--- {name} Results ---\n{output.getvalue()}")
                    ui.notify(f'{name} Completed', type='positive')

                ui.button('DB Test', on_click=lambda: run_test_logic(db_test, 'DB Test')).props('outline')
                ui.button('Parser Test', on_click=lambda: run_test_logic(parser_test, 'Parser Test')).props('outline')
                ui.button('Run All', on_click=lambda: run_test_logic(run_all_tests, 'Full Pipeline')).props('color=red')

            test_log = ui.log(max_lines=1000).classes('w-full h-80 bg-black text-green-400 font-mono p-2 text-xs')

# --- API Endpoints ---

@fastapi_app.post("/run_all_tests")
async def api_tests(request: Request):
    data = await request.json()
    verbose = data.get("verbose", False)
    run_all_tests(verbose)
    return {"status": "Pipeline finished"}

ui.run_with(fastapi_app, mount_path='/')

if __name__ in {"__main__", "__mp_main__"}:
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000)