import { render, screen } from '@testing-library/react';
import Home from '../app/page';



describe('Home Page', () => {
  it('renders hero headline', () => {
    render(<Home />);
    const heading = screen.getByRole('heading', { name: /accelerate test automation/i });
    expect(heading).toBeInTheDocument();
  });

  it('has skip link target main-content landmark', () => {
    
    render(<Home />);
    
    expect(screen.getByText(/Enterprise NLP Platform/i)).toBeInTheDocument();
  });
});
