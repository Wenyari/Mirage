import { createBrowserRouter, Navigate } from 'react-router-dom';

import AdminGuard from '@/components/auth/AdminGuard';
// Admin Imports
import AdminLayout from '@/layouts/AdminLayout';
import UserLayout from '@/layouts/UserLayout';
import CDKManager from '@/pages/admin/CDKManager';
import Dashboard from '@/pages/admin/Dashboard';
import KeyPool from '@/pages/admin/KeyPool';
import Login from '@/pages/admin/Login';
import ModelConfigManager from '@/pages/admin/ModelConfigManager';
import ModelManager from '@/pages/admin/ModelManager';
import Playground from '@/pages/admin/Playground';
import UserManager from '@/pages/admin/UserManager';
import UserLogin from '@/pages/auth/UserLogin';
import UserRegister from '@/pages/auth/UserRegister';
import Agents from '@/pages/user/explore/Agents';
import Prompts from '@/pages/user/explore/Prompts';
import Workflows from '@/pages/user/explore/Workflows';
import Home from '@/pages/user/Home';
import ModelSquare from '@/pages/user/ModelSquare';
import Community from '@/pages/user/more/Community';
import Events from '@/pages/user/more/Events';
import Updates from '@/pages/user/more/Updates';
import Chat from '@/pages/user/playground/Chat';
import VideoGeneration from '@/pages/user/playground/VideoGeneration';
import Credits from '@/pages/user/settings/Credits';

export const router = createBrowserRouter([
  // Admin Routes
  {
    path: '/wadminw/login',
    element: <Login />,
  },
  {
    path: '/wadminw',
    element: (
      <AdminGuard>
        <AdminLayout />
      </AdminGuard>
    ),
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
        path: 'model-configs',
        element: <ModelConfigManager />,
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

  // User Routes
  {
    path: '/login',
    element: <UserLogin />,
  },
  {
    path: '/register',
    element: <UserRegister />,
  },
  {
    path: '/',
    element: <UserLayout />,
    children: [
      {
        index: true,
        element: <Home />,
      },
      {
        path: 'models',
        element: <ModelSquare />,
      },
      {
        path: 'explore',
        children: [
          {
            index: true,
            element: <Navigate to="/explore/prompts" replace />,
          },
          {
            path: 'prompts',
            element: <Prompts />,
          },
          {
            path: 'agents',
            element: <Agents />,
          },
          {
            path: 'workflows',
            element: <Workflows />,
          },
        ],
      },
      {
        path: 'playground',
        children: [
          {
            index: true,
            element: <Navigate to="/playground/chat" replace />,
          },
          {
            path: 'chat',
            element: <Chat />,
          },
          {
            path: 'video',
            element: <VideoGeneration />,
          },
        ],
      },
      {
        path: 'setting',
        children: [
          {
            path: 'credits',
            element: <Credits />,
          },
        ],
      },
      {
        path: 'more',
        children: [
          {
            index: true,
            element: <Navigate to="/more/updates" replace />,
          },
          {
            path: 'updates',
            element: <Updates />,
          },
          {
            path: 'events',
            element: <Events />,
          },
          {
            path: 'community',
            element: <Community />,
          },
          {
            path: 'setting',
            children: [
              {
                path: 'credits',
                element: <Credits />,
              },
            ],
          },
        ],
      },
    ],
  },
  {
    path: '*',
    element: <Navigate to="/" replace />,
  },
]);
