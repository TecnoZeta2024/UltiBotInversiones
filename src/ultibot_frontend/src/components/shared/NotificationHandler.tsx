import { Toaster, toast } from 'react-hot-toast';

const NotificationHandler = () => {
  return (
    <Toaster
      position="top-right"
      toastOptions={{
        // Define default options
        className: '',
        duration: 5000,
        style: {
          background: '#363636',
          color: '#fff',
        },

        // Default options for specific types
        success: {
          duration: 3000,
        },
        error: {
            duration: 5000,
        }
      }}
    />
  );
};

export const notify = {
  success: (message: string) => toast.success(message),
  error: (message: string) => toast.error(message),
  info: (message: string) => toast(message),
};

export default NotificationHandler;
