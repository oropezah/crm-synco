from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json

app = FastAPI()

# Permitir conexiones CORS desde localhost o Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Token de verificación que inventas tú (debe coincidir en la app de Meta)
VERIFY_TOKEN = "mi_token_secreto_synco_123"

# Conexiones WebSocket activas (tu CRM)
active_connections: list[WebSocket] = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)

# 1. Endpoint para verificación inicial del Webhook por parte de Meta (GET)
@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook verificado con éxito por Meta!")
        return Response(content=challenge, media_type="text/plain")
    return Response(content="Error de verificación", status_code=403)

# 2. Endpoint donde Meta envía las notificaciones en tiempo real (POST)
@app.post("/webhook")
async def receive_webhook(request: Request):
    data = await request.json()
    print("📩 Webhook recibido de Meta:", json.dumps(data, indent=2))

    # Notificar a la interfaz de Synco CRM vía WebSocket
    for connection in active_connections:
        try:
            await connection.send_text(json.dumps({"event": "new_message", "data": data}))
        except Exception as e:
            print("Error enviando por WebSocket:", e)

    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)