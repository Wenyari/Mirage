import { createBrowserRouter, Navigate } from 'react-router-dom';

import AdminLayout from '@/layouts/AdminLayout';
import CDKManager from '@/pages/admin/CDKManager';
import Dashboard from '@/pages/admin/Dashboard';
import KeyPool from '@/pages/admin/KeyPool';
import ModelManager from '@/pages/admin/ModelManager';
import Playground from '@/pages/admin/Playground';
import UserManager from '@/pages/admin/UserManager';

export const router = createBrowserRouter([
  {
    path: '/wadminw',
    element: <AdminLayout />,
    children: [
      {
        index: true,
        element: <Navigate to="/wadminw/dashboard" replace />,
      },
      {
        path: 'dashboard',
        element: <Dashboard />,
      },
      {
        path: 'users',
        element: <UserManager />,
      },
      {
        path: 'cdk',
        element: <CDKManager />,
      },
      {
        path: 'keys',
        element: <KeyPool />,
      },
      {
        path: 'models',
        element: <ModelManager />,
      },
      {
        path: 'playground',
        element: <Playground />,
      },
    ],
  },
  {
    path: '*',
    element: <Navigate to="/wadminw/dashboard" replace />,
  },
]);
