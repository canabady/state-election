import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider, createRouter, createBrowserHistory } from '@tanstack/react-router'
import { routeTree } from './routeTree.gen'
import { NotFound } from "./components/common/NotFound";
import { Loader } from "./components/common/Loader";

const queryClient = new QueryClient();

const browserHistory = createBrowserHistory()

const router = createRouter({
  routeTree,
  history: browserHistory,
  defaultPreload: 'intent',
  context: { queryClient },
  defaultNotFoundComponent: NotFound,
  defaultPendingComponent: Loader,
})

// Register the router instance
declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
}

export default App;
