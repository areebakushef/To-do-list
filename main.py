import json
import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import itertools
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="Add_your_own_secret_key_here") #===========>Add_your_own_secret_key_here
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


class Task(BaseModel):
    id: int
    title: str
    description: Optional[str] = ""
    due_date: Optional[str] = ""  # New field
    completed: bool = False

TASKS_FILE = "tasks.json"

def load_tasks():
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "r") as f:
            data = json.load(f)
            return [Task(**item) for item in data]
    return []

def save_tasks():
    with open(TASKS_FILE, "w") as f:
        json.dump([task.dict() for task in tasks], f, indent=4)

tasks = load_tasks()
id_counter = itertools.count(max([task.id for task in tasks], default=0) + 1)

@app.get("/", response_class=HTMLResponse)
def read_tasks(request: Request):
    message = request.session.pop("message", None)
    return templates.TemplateResponse("index.html", {"request": request, "tasks": tasks, "message": message})

@app.post("/add")
def add_task(request: Request, title: str = Form(...), description: str = Form(""), due_date: str = Form("")):
    task = Task(id=next(id_counter), title=title, description=description, due_date=due_date)
    tasks.append(task)
    save_tasks()
    request.session["message"] = "Task added successfully!"
    return RedirectResponse("/", status_code=303)

@app.get("/edit/{task_id}", response_class=HTMLResponse)
def edit_task_form(request: Request, task_id: int):
    task = next((t for t in tasks if t.id == task_id), None)
    return templates.TemplateResponse("edit.html", {"request": request, "task": task})

@app.post("/edit/{task_id}")
def edit_task(request: Request, task_id: int, title: str = Form(...), description: str = Form(""), due_date: str = Form(""), completed: Optional[bool] = Form(False)):
    for task in tasks:
        if task.id == task_id:
            task.title = title
            task.description = description
            task.due_date = due_date
            task.completed = completed
            break
    save_tasks()
    request.session["message"] = "Task updated successfully!"
    return RedirectResponse("/", status_code=303)

@app.post("/delete/{task_id}")
def delete_task(request: Request, task_id: int):
    global tasks
    tasks = [t for t in tasks if t.id != task_id]
    save_tasks()
    request.session["message"] = "Task deleted successfully!"
    return RedirectResponse("/", status_code=303)

@app.post("/mark_complete/{task_id}")
def mark_task_complete(task_id: int):
    for task in tasks:
        if task.id == task_id:
            task.completed = True
            break
    save_tasks()
    return RedirectResponse("/", status_code=303)

@app.get("/completed", response_class=HTMLResponse)
def show_completed_tasks(request: Request):
    completed_tasks = [task for task in tasks if task.completed]
    return templates.TemplateResponse("completed.html", {"request": request, "tasks": completed_tasks})

@app.get("/incomplete", response_class=HTMLResponse)
def show_incomplete_tasks(request: Request):
    incomplete_tasks = [task for task in tasks if not task.completed]
    return templates.TemplateResponse("incomplete.html", {"request": request, "tasks": incomplete_tasks})
