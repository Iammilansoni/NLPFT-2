import type { Meta, StoryObj } from '@storybook/react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from './enhanced-card';
import { Button } from './enhanced-button';


const meta = {
  title: 'UI/Enhanced Card',
  component: Card,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    hover: {
      control: 'boolean',
      description: 'Enable hover elevation effect',
    },
    gradient: {
      control: 'boolean',
      description: 'Enable glassmorphism gradient',
    },
  },
} satisfies Meta<typeof Card>;

export default meta;
type Story = StoryObj<typeof meta>;


export const Basic: Story = {
  args: {
    children: (
      <>
        <CardHeader>
          <CardTitle>Card Title</CardTitle>
          <CardDescription>This is a card description</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            This is the card content. You can put any content here.
          </p>
        </CardContent>
      </>
    ),
  },
};


export const WithHover: Story = {
  args: {
    hover: true,
    children: (
      <>
        <CardHeader>
          <CardTitle>Hover Me</CardTitle>
          <CardDescription>This card has a hover elevation effect</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm">Move your cursor over this card to see the effect.</p>
        </CardContent>
      </>
    ),
  },
};


export const WithGradient: Story = {
  args: {
    gradient: true,
    children: (
      <>
        <CardHeader>
          <CardTitle>Glassmorphism Card</CardTitle>
          <CardDescription>Beautiful gradient with blur effect</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm">This card uses a glassmorphism effect with gradient borders.</p>
        </CardContent>
      </>
    ),
  },
};


export const Complete: Story = {
  args: {
    hover: true,
    children: (
      <>
        <CardHeader>
          <CardTitle>Complete Card</CardTitle>
          <CardDescription>With header, content, and footer</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <p className="text-sm">
              This card demonstrates all available sections: header, content, and footer.
            </p>
            <div className="flex gap-2">
              <div className="flex-1 p-3 bg-muted rounded-lg">
                <div className="text-2xl font-bold">87.8%</div>
                <div className="text-xs text-muted-foreground">Success Rate</div>
              </div>
              <div className="flex-1 p-3 bg-muted rounded-lg">
                <div className="text-2xl font-bold">20+</div>
                <div className="text-xs text-muted-foreground">Functions</div>
              </div>
            </div>
          </div>
        </CardContent>
        <CardFooter className="gap-2">
          <Button variant="default" size="sm">
            Primary Action
          </Button>
          <Button variant="outline" size="sm">
            Secondary
          </Button>
        </CardFooter>
      </>
    ),
  },
};


export const Grid: Story = {
  render: () => (
    <div className="grid grid-cols-3 gap-4 max-w-4xl">
      {[1, 2, 3].map((i) => (
        <Card key={i} hover>
          <CardHeader>
            <CardTitle>Feature {i}</CardTitle>
            <CardDescription>Description for feature {i}</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm">Some content about this feature.</p>
          </CardContent>
        </Card>
      ))}
    </div>
  ),
};
