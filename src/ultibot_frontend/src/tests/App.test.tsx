import { render, screen } from '@testing-library/react';
import App from '../App';
import { vi } from 'vitest';

// Mock Highcharts to prevent errors in JSDOM environment
vi.mock('highcharts-react-official', () => ({
  default: () => <div>Highcharts Mock</div>,
}));

vi.mock('highcharts', () => ({
  default: {
    chart: vi.fn(),
  },
}));

describe('App', () => {
  it('renders the main App component', () => {
    render(<App />);
    // The App component has a div with className="App"
    const appElement = document.querySelector('.App');
    expect(appElement).toBeInTheDocument();
  });
});
