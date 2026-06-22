import { createContext, useContext, useEffect, useState } from 'react';
import { useAuth } from './AuthContext'; // assuming AuthContext provides token & userId

const NotificationContext = createContext();

export const useNotifications = () => useContext(NotificationContext);

export const NotificationProvider = ({ children }) => {
  const { token, userId } = useAuth();
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    if (!token) return;
    const ws = new WebSocket(`ws://${window.location.host}/ws/notifications?token=${token}`);
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setNotifications((prev) => [...prev, data]);
      } catch (e) {
        console.error('Invalid notification payload', e);
      }
    };
    ws.onclose = () => console.warn('Notification WS closed');
    ws.onerror = (err) => console.error('Notification WS error', err);
    return () => ws.close();
  }, [token]);

  const clear = () => setNotifications([]);

  return (
    <NotificationContext.Provider value={{ notifications, clear }}>
      {children}
    </NotificationContext.Provider>
  );
};
