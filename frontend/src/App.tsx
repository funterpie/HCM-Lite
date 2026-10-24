import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '@/auth/AuthProvider';
import { ToastProvider } from '@/components/ui/Toast';
import { AppRoutes } from '@/routes';

export function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ToastProvider>
          <AppRoutes />
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
