import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './enhanced-button';
import { ArrowRight, Download, Loader2 } from 'lucide-react';


const meta = {
  title: 'UI/Enhanced Button',
  component: Button,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'destructive', 'outline', 'secondary', 'ghost', 'link'],
    },
    size: {
      control: 'select',
      options: ['sm', 'default', 'lg', 'xl', 'icon'],
    },
    loading: {
      control: 'boolean',
    },
    disabled: {
      control: 'boolean',
    },
  },
} satisfies Meta<typeof Button>;

export default meta;
type Story = StoryObj<typeof meta>;


export const Default: Story = {
  args: {
    children: 'Click Me',
    variant: 'default',
    size: 'default',
  },
};


export const WithIcon: Story = {
  args: {
    children: (
      <>
        Get Started
        <ArrowRight className="ml-2 w-4 h-4" />
      </>
    ),
    variant: 'default',
    size: 'lg',
  },
};


export const Loading: Story = {
  args: {
    loading: true,
    children: 'Downloading...',
  },
};


export const Outline: Story = {
  args: {
    children: 'Outline Button',
    variant: 'outline',
  },
};


export const Ghost: Story = {
  args: {
    children: 'Ghost Button',
    variant: 'ghost',
  },
};


export const Destructive: Story = {
  args: {
    children: 'Delete Account',
    variant: 'destructive',
  },
};


export const Disabled: Story = {
  args: {
    children: 'Disabled Button',
    disabled: true,
  },
};


export const Sizes: Story = {
  render: () => (
    <div className="flex flex-col gap-4 items-start">
      <Button size="sm">Small</Button>
      <Button size="default">Default</Button>
      <Button size="lg">Large</Button>
      <Button size="xl">Extra Large</Button>
      <Button size="icon">
        <Download className="w-4 h-4" />
      </Button>
    </div>
  ),
};


export const AllVariants: Story = {
  render: () => (
    <div className="flex flex-wrap gap-4">
      <Button variant="default">Default</Button>
      <Button variant="secondary">Secondary</Button>
      <Button variant="outline">Outline</Button>
      <Button variant="ghost">Ghost</Button>
      <Button variant="link">Link</Button>
      <Button variant="destructive">Destructive</Button>
    </div>
  ),
};
