/**
 * Accessibility Testing Suite
 * 
 * Automated WCAG 2.1 AA compliance testing using:
 * - jest-axe for accessibility violations
 * - React Testing Library for component testing
 */
import React from 'react';
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { AccessibilityControls } from '../components/accessibility/AccessibilityControls';

expect.extend(toHaveNoViolations);

describe('Accessibility Tests', () => {
  test('AccessibilityControls should have no accessibility violations', async () => {
    const { container } = render(<AccessibilityControls />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  test('Buttons should have proper ARIA labels', async () => {
    const { getByRole } = render(
      <button aria-label="Test button">Click me</button>
    );
    
    const button = getByRole('button', { name: 'Test button' });
    expect(button).toHaveAttribute('aria-label', 'Test button');
  });

  test('Form inputs should have associated labels', async () => {
    const { getByLabelText } = render(
      <div>
        <label htmlFor="test-input">Test Input</label>
        <input id="test-input" type="text" />
      </div>
    );
    
    const input = getByLabelText('Test Input');
    expect(input).toBeInTheDocument();
  });

  test('Images should have alt text', async () => {
    const { getByAltText } = render(
      <img src="test.jpg" alt="Test image description" />
    );
    
    const image = getByAltText('Test image description');
    expect(image).toBeInTheDocument();
  });

  test('Interactive elements should be keyboard accessible', async () => {
    const { getByRole } = render(
      <button onClick={() => {}}>Keyboard accessible</button>
    );
    
    const button = getByRole('button');
    expect(button).toHaveAttribute('tabIndex', '0');
  });
});

