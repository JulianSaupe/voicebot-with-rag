export interface WebSocketMessage {
    type: string;
    data?: any;
    id?: string;
}

export interface WebSocketEventListener {
    (message: WebSocketMessage): void;
}

export class WebSocketHandler {
    private socket: WebSocket | null = null;
    private isConnected: boolean = false;
    private eventListeners: Map<string, WebSocketEventListener[]> = new Map();
    private reconnectAttempts: number = 0;
    private maxReconnectAttempts: number = 5;
    private reconnectDelay: number = 1000;

    constructor(private serverUrl: string) {}

    async connect(): Promise<void> {
        return new Promise((resolve, reject) => {
            try {
                this.socket = new WebSocket(this.serverUrl);

                this.socket.onopen = () => {
                    console.log('🔌 WebSocket connected to backend');
                    this.isConnected = true;
                    this.reconnectAttempts = 0;
                    resolve();
                };

                this.socket.onmessage = (event) => {
                    try {
                        const message: WebSocketMessage = JSON.parse(event.data);
                        this.handleMessage(message);
                    } catch (error) {
                        console.error('❌ Error parsing WebSocket message:', error);
                    }
                };

                this.socket.onclose = (event) => {
                    console.log('🔌 WebSocket connection closed:', event);
                    this.isConnected = false;
                    this.handleReconnect();
                };

                this.socket.onerror = (error) => {
                    console.error('❌ WebSocket error:', error);
                    this.isConnected = false;
                    reject(error);
                };

            } catch (error) {
                reject(error);
            }
        });
    }

    private handleMessage(message: WebSocketMessage): void {
        const listeners = this.eventListeners.get(message.type);
        if (listeners) {
            listeners.forEach(listener => listener(message));
        }
    }

    private async handleReconnect(): Promise<void> {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`🔄 Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
            
            setTimeout(async () => {
                try {
                    await this.connect();
                } catch (error) {
                    console.error('❌ Reconnection failed:', error);
                }
            }, this.reconnectDelay * this.reconnectAttempts);
        } else {
            console.error('❌ Max reconnection attempts reached');
        }
    }

    addEventListener(messageType: string, listener: WebSocketEventListener): void {
        if (!this.eventListeners.has(messageType)) {
            this.eventListeners.set(messageType, []);
        }
        this.eventListeners.get(messageType)!.push(listener);
    }

    removeEventListener(messageType: string, listener: WebSocketEventListener): void {
        const listeners = this.eventListeners.get(messageType);
        if (listeners) {
            const index = listeners.indexOf(listener);
            if (index > -1) {
                listeners.splice(index, 1);
            }
        }
    }

    sendMessage(message: WebSocketMessage): void {
        if (this.socket && this.isConnected && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(message));
        } else {
            console.warn('⚠️ Cannot send message: WebSocket not connected');
        }
    }


    disconnect(): void {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
        this.isConnected = false;
        this.eventListeners.clear();
    }

    get connected(): boolean {
        return this.isConnected;
    }
}