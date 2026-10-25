/**
 * @file App.tsx
 * @description Application root component establishing Router, Auth, and Toast providers.
 */

import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '@/auth/AuthProvider';
import { ToastProvider } from '@/components/ui/Toast';
import { AppRoutes } from '@/routes';

export function App() {
  return (
    <BrowserRouter>
      {/* Provides authenticated session, current role, and React Query cache */}
      <AuthProvider>
        {/* Provides global animated notification toasts */}
        <ToastProvider>
          {/* Main routed application view hierarchy */}
          <AppRoutes />
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
