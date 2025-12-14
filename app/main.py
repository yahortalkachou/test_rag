import os
import io
import contextlib
import httpx
from datetime import datetime
from fastapi import FastAPI, Request
from nicegui import ui, run
import uvicorn
from dotenv import load_dotenv

from app.tests import run_all_tests
from app.tests import db_test
from app.tests import parsing_test
from app.tests import search_test
from app.vector_db import VectorDBType, VectorDBFactory, ConnectionParams, CustomEmbedder
from app.vector_db import SearchResult 

load_dotenv()

fastapi_app = FastAPI()

# --- UI Logic ---
def results_response_fromatting (results: list[SearchResult]) -> dict:
    ret = []
    ret = [res.to_dict for res in results]
    return ret

    pass
class State:
    search_mode = 'Personal Data'
    test_output = ""
    has_results = False
    search_in_progress = False
    current_results = []

state = State()

settings_file = os.getenv(f"PROJECT_DATA_TEST_SETTINGS")
personal_collection = os.getenv(f"TEST_PERSONAL_DATA_COLLECTION_NAME") 
project_collection = os.getenv(f"TEST_PROJECT_DATA_COLLECTION_NAME") 
host = os.getenv("QDRANT_HOST")
port = int(os.getenv("QDRANT_PORT", 6333))

params = ConnectionParams(host=host, port=port)
embedder = CustomEmbedder(os.getenv("EMBEDDING_MODEL_NAME"))
db_manager = VectorDBFactory.create_manager(
    db_type=VectorDBType.QDRANT,
    embedder=embedder
)

db_manager.connect(params)

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
                    languages_select = ui.select(
                        ['english b2', 'japanese a2', 'german b1', "polish b1"], 
                        label='Languages', 
                        multiple=True
                    ).classes('w-full')
                    level_select = ui.select(
                        ['junior', 'mid', 'senior'], 
                        label='Candidate Level', 
                        multiple=True
                    ).classes('w-full')
                
                # Project Roles (Project/Aggregate)
                with ui.column().bind_visibility_from(state, 'search_mode', 
                    backward=lambda m: m in ['Project Data', 'Aggregate Both']):
                    roles_select = ui.select(
                        ['machine learning engineer', 'data scientist', 'ai architect'], 
                        label='Project Roles', 
                        multiple=True
                    ).classes('w-full')

            async def execute_search():
                if not query_input.value :#or state.search_in_progress:
                    return
                
                state.search_in_progress = True
                search_btn.disable()
                
                try:
                    if state.search_mode == 'Personal Data':
                        endpoint = "/search/personal"
                    elif state.search_mode == 'Project Data':
                        endpoint = "/search/project"
                    else:  # Aggregate Both
                        endpoint = "/search/aggregate"
                    
                    filters = {}
                    
                    if state.search_mode == 'Personal Data':
                        if languages_select.value:
                            filters["languages"] = {
                                "must": True,
                                "values": languages_select.value
                            }
                        if level_select.value:
                            filters["level"] = {
                                "must": True,
                                "values": level_select.value
                            }
                    
                    elif state.search_mode == 'Project Data':
                        if roles_select.value:
                            filters["roles"] = {
                                "must": True,
                                "values": roles_select.value
                            }
                    
                    async with httpx.AsyncClient() as client:
                        response = await client.post(
                            f"http://localhost:8000{endpoint}",
                            json={
                                "query": query_input.value,
                                "filters": filters if filters else None
                            },
                            timeout=30.0
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            state.current_results = data.get("results", [])
                            state.has_results = len(state.current_results) > 0
                            
                            update_results_display()
                            
                            ui.notify(f"Found {len(state.current_results)} results", type='positive')
                        else:
                            error_msg = data.get("error", response.text) if response.status_code == 400 else response.text
                            ui.notify(f"Search error: {error_msg}", type='negative')
                            state.has_results = False
                            
                except Exception as e:
                    ui.notify(f"Search error: {str(e)}", type='negative')
                    state.has_results = False
                finally:
                    state.search_in_progress = False
                    search_btn.enable()
            
            with ui.row().classes('w-full items-center mt-6'):
                search_btn = ui.button(
                    'EXECUTE SEARCH', 
                    on_click=execute_search
                ).classes('flex-1 h-12 text-lg')
                ui.spinner(size='lg').bind_visibility_from(state, 'search_in_progress')

        # --- RIGHT COLUMN: Results & Testing Dashboard ---
        with ui.column().classes('w-2/3 p-6 gap-6'):
            
            results_display = ui.column().classes('w-full')
            
            def update_results_display():
                results_display.clear()
                
                with results_display:
                    if not state.has_results:
                        ui.label('No search performed yet.').classes('text-gray-400')
                        return
                    
                    ui.label(f'Search Results ({len(state.current_results)} found)').classes('text-lg font-bold mb-4')
                    
                    for i, result in enumerate(state.current_results):
                        with ui.card().classes('w-full mb-4'):
                            with ui.row().classes('w-full items-start'):
                                with ui.column().classes('flex-1'):
                                    # ID и score
                                    ui.label(f"{i+1}. Result ID: {result.get('id', 'N/A')}").classes('font-semibold')
                                    
                                    # Score
                                    score = result.get('score', 0)
                                    with ui.row().classes('items-center gap-2'):
                                        ui.label(f"Score: {score:.3f}")
                                        if score > 0.7:
                                            ui.badge('High match', color='green')
                                        elif score > 0.4:
                                            ui.badge('Medium match', color='orange')
                                        else:
                                            ui.badge('Low match', color='red')
                                    
                                    document = result.get('document', '')
                                    if document:
                                        preview = document[:200] + "..." if len(document) > 200 else document
                                        ui.label('Preview:').classes('text-sm font-medium mt-2')
                                        ui.label(preview).classes('text-sm text-gray-600 italic bg-gray-50 p-2 rounded')
                                    
                                    metadata = result.get('metadata', {})
                                    if metadata:
                                        with ui.expansion('Metadata', icon='info').classes('w-full'):
                                            for key, value in list(metadata.items())[:5]:  # Первые 5 полей
                                                with ui.row().classes('text-sm'):
                                                    ui.label(f"{key}: ").classes('font-medium')
                                                    ui.label(str(value)).classes('text-gray-600')
                                
                                with ui.column().classes('gap-2'):
                                    ui.button('View Full', on_click=lambda r=result: show_full_result(r)).props('outline size=sm')
            
            def show_full_result(result):
                """Show full result"""
                with ui.dialog() as dialog, ui.card().classes('w-full max-w-2xl'):
                    ui.label('Full Result').classes('text-xl font-bold mb-4')
                    
                    ui.label(f"ID: {result.get('id', 'N/A')}").classes('font-medium')
                    ui.label(f"Score: {result.get('score', 0):.3f}").classes('font-medium')
                    
                    if result.get('distance'):
                        ui.label(f"Distance: {result.get('distance', 0):.3f}").classes('font-medium')
                    
                    ui.label('Document:').classes('font-medium mt-4')
                    document = result.get('document', '')
                    ui.textarea(value=document).classes('w-full h-48').props('readonly autogrow')
                    
                    metadata = result.get('metadata', {})
                    if metadata:
                        ui.label('Metadata:').classes('font-medium mt-4')
                        ui.json_editor({'content': {'json': metadata}}).classes('w-full h-64')
                    
                    ui.button('Close', on_click=dialog.close).props('flat mt-4')
                
                dialog.open()
            
            update_results_display()
            
            ui.separator()
            ui.label('Testing Dashboard').classes('text-xl font-bold')
            
            with ui.row().classes('w-full gap-2'):
                async def run_test_logic(func, name, storage:str | None = None):
                    ui.notify(f'Running {name}...')
                    output = io.StringIO()
                    with contextlib.redirect_stdout(output):
                        if not storage:
                            await run.io_bound(func, verbose=True)
                        else:
                            await run.io_bound(func, verbose=True, storage=storage)
                            
                    test_log.push(f"--- {name} Results ---\n{output.getvalue()}")
                    ui.notify(f'{name} Completed', type='positive')

                ui.button('DB Test', on_click=lambda: run_test_logic(db_test, 'DB Test')).props('outline')
                ui.button('Parser Test', on_click=lambda: run_test_logic(parsing_test, 'Parser Test')).props('outline')
                ui.button('Project data search test', on_click=lambda: run_test_logic(search_test, 'Project data search test', "PROJECT_DATA")).props('outline')
                ui.button('Personal data searching test', on_click=lambda: run_test_logic(search_test, 'Personal data searching test', "PERSONAL_DATA")).props('outline')
                ui.button('Run All', on_click=lambda: run_test_logic(run_all_tests, 'Full Pipeline')).props('color=red')

            test_log = ui.log(max_lines=1000).classes('w-full h-80 bg-black text-green-400 font-mono p-2 text-xs')

# --- API Endpoints ---

@fastapi_app.post("/run_all_tests")
async def api_tests(request: Request):
    data = await request.json()
    verbose = data.get("verbose", False)
    run_all_tests(verbose)
    return {"status": "Pipeline finished"}

@fastapi_app.post("/search/personal")
async def api_search_personal(request: Request):
    """personal data search"""
    try:
        data = await request.json()
        query_text = data.get("query", "")
        filters = data.get("filters", {})
        
        if not query_text:
            return {"error": "Query parameter is required"}, 400
        
        if filters:
            results = db_manager.filtered_search(
                collection_name=personal_collection,
                query=query_text,
                filters=filters,
                limit=15
            )
            search_type = "filtered"
        else:
            embeddings = embedder.get_embeddings([query_text])[0]
            results = db_manager.search(
                collection_name=personal_collection,
                query_embedding=embeddings,
                limit=15
            )
            search_type = "standard"

        return {
            "status": "success",
            "query": query_text,
            "collection": personal_collection,
            "mode": "personal",
            "search_type": search_type,
            "filters": filters,
            "results_count": len(results),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": str(e)}, 500

@fastapi_app.post("/search/project")
async def api_search_project(request: Request):
    """project data search"""
    try:
        data = await request.json()
        query_text = data.get("query", "")
        filters = data.get("filters", {})
        
        if not query_text:
            return {"error": "Query parameter is required"}, 400
        
        if filters:
            results = db_manager.filtered_search(
                collection_name=project_collection,
                query=query_text,
                filters=filters,
                limit=15
            )
            search_type = "filtered"
        else:
            embeddings = embedder.get_embeddings([query_text])[0]
            results = db_manager.search(
                collection_name=project_collection,
                query_embedding=embeddings,
                limit=15
            )
            search_type = "standard"
        formatted_results = results
        
        return {
            "status": "success",
            "query": query_text,
            "collection": project_collection,
            "mode": "project",
            "search_type": search_type,
            "filters": filters,
            "results_count": len(formatted_results),
            "results": formatted_results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": str(e)}, 500

@fastapi_app.post("/search/aggregate")
async def api_search_aggregate(request: Request):
    """not implemented"""
    return {
        "error": "Fusion mechanics has not been implemented yet.",
        "message": "Please select either 'Personal Data' or 'Project Data' mode for now.",
        "status": "not_implemented"
    }, 400

ui.run_with(fastapi_app, mount_path='/')

if __name__ in {"__main__", "__mp_main__"}:
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000)