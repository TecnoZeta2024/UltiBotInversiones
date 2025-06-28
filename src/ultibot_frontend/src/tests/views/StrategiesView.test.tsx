import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import StrategiesView from '@/views/StrategiesView';
import apiClient from '@/lib/apiClient';

// Mock the apiClient module to ensure apiClient.get is a mock function
vi.mock('@/lib/apiClient', () => ({
  default: {
    get: vi.fn(),
  },
}));

// Mock the magicui/file-tree components
vi.mock('@/components/magicui/file-tree', () => {
  return {
    Tree: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
    Folder: ({ children, element, value }: { children: React.ReactNode; element: string; value: string }) => {
      const [expanded, setExpanded] = React.useState(false);
      return (
        <div>
          <button onClick={() => setExpanded(!expanded)}>{element}</button>
          {expanded && children}
        </div>
      );
    },
    File: ({ children, handleSelect, value }: { children: React.ReactNode; handleSelect: (id: string) => void; value: string }) => {
      return <button onClick={() => handleSelect(value)}>{children}</button>;
    },
  };
});

const mockStrategies = [
  {
    id: 'src/ultibot_backend/strategies/long_term', // Keep full path for folder ID
    name: 'long_term',
    children: [
      { id: 'src/ultibot_backend/strategies/long_term/mean_reversion.py', name: 'mean_reversion.py', children: [] }, // Keep full path for file ID
    ],
  },
];

describe('StrategiesView', () => {
  let consoleErrorSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    // Reset all mocks before each test
    vi.resetAllMocks();
    // Silence console.error during tests
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    // Restore console.error after each test
    consoleErrorSpy.mockRestore();
  });

  it('should show loading state initially', () => {
    vi.mocked(apiClient.get).mockReturnValue(new Promise(() => {})); // Unresolved promise
    render(<StrategiesView />);
    expect(screen.getByText('Loading strategies...')).toBeInTheDocument();
  });

  it('should display strategies after successful fetch', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockStrategies });
    render(<StrategiesView />);
    
    // Find and click the folder to expand it
    const folderElement = await screen.findByText('long_term');
    fireEvent.click(folderElement);

    expect(folderElement).toBeInTheDocument();
    expect(await screen.findByText('mean_reversion.py')).toBeInTheDocument();
  });

  it('should display error message on fetch failure', async () => {
    vi.mocked(apiClient.get).mockRejectedValue(new Error('Network Error'));
    render(<StrategiesView />);

    expect(await screen.findByText('Failed to fetch strategies. Please make sure the backend is running.')).toBeInTheDocument();
  });

  it('should fetch and display file content on file click', async () => {
    const fileContent = "print('Hello, World!')";
    
    // Mock the handleSelect function directly
    const mockHandleSelect = vi.fn();

    vi.mocked(apiClient.get)
      .mockResolvedValueOnce({ data: mockStrategies }) // For the initial tree fetch
      .mockResolvedValueOnce({ data: { content: fileContent } }); // For the file content fetch

    render(<StrategiesView />);

    // Find and click the folder to expand it
    const folderElement = await screen.findByText('long_term');
    fireEvent.click(folderElement);

    // Find the file element (which is a button in the mocked component)
    const fileButton = await screen.findByRole('button', { name: 'mean_reversion.py' });
    expect(fileButton).toBeInTheDocument();

    // Simulate the click on the file button, which should trigger handleSelect
    fireEvent.click(fileButton);

    // Wait for the textarea to be present
    const textarea = await screen.findByPlaceholderText('Select a file to view its content...');
    expect(textarea).toBeInTheDocument();

    // Verify that the correct API calls were made
    await waitFor(() => {
      expect(vi.mocked(apiClient.get)).toHaveBeenCalledWith('/strategies/files');
      expect(vi.mocked(apiClient.get)).toHaveBeenCalledWith('/strategies/files/long_term/mean_reversion.py');
    });
  });
});
