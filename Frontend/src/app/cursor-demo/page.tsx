import { Metadata } from "next";
import {
  ExampleButton,
  ExampleCard,
  ExampleLoadingButton,
  ExampleInput,
  ExampleDisabledButton
} from "@/components/examples/cursor-examples";

export const metadata: Metadata = {
  title: "Cursor Demo",
  description: "Demonstration of custom cursor animations",
};

export default function CursorDemoPage() {
  return (
    <div className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto space-y-8">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Custom Cursor Demo
          </h1>
          <p className="text-lg text-muted-foreground">
            Move your mouse around to see the custom cursor animations in action
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          
          <div className="card p-6 space-y-4">
            <h3 className="text-xl font-semibold">Hover Effects</h3>
            <p className="text-sm text-muted-foreground">
              Hover over these elements to see the cursor change
            </p>
            <div className="space-y-3">
              <ExampleButton />
              <button className="btn-primary w-full cursor-interactive">
                Another Button
              </button>
              <a href="#" className="block text-blue-600 hover:text-blue-800 cursor-interactive">
                Link with hover effect
              </a>
            </div>
          </div>

          <div className="card p-6 space-y-4">
            <h3 className="text-xl font-semibold">Custom States</h3>
            <p className="text-sm text-muted-foreground">
              Different cursor states for different interactions
            </p>
            <div className="space-y-3">
              <ExampleLoadingButton />
              <ExampleDisabledButton />
              <div className="p-2 border rounded cursor-interactive" data-cursor="hover">
                <span>Custom hover area</span>
              </div>
            </div>
          </div>

          <div className="card p-6 space-y-4">
            <h3 className="text-xl font-semibold">Text Inputs</h3>
            <p className="text-sm text-muted-foreground">
              Text cursor appears over input fields
            </p>
            <div className="space-y-3">
              <ExampleInput />
              <textarea
                placeholder="Type your message..."
                className="w-full border p-2 rounded h-20 resize-none"
                data-cursor="text"
              />
              <div
                contentEditable
                className="border p-2 rounded min-h-[60px]"
                data-cursor="text"
              >
                Editable content area
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <ExampleCard />
            
            <div className="card p-4 cursor-interactive">
              <h4 className="font-semibold">Regular Card</h4>
              <p className="text-sm text-muted-foreground">
                Hover over this card to see the cursor change
              </p>
            </div>

            <div className="card p-4 cursor-interactive" data-cursor="disabled">
              <h4 className="font-semibold opacity-50">Disabled Card</h4>
              <p className="text-sm text-muted-foreground opacity-50">
                This card shows the disabled cursor state
              </p>
            </div>
          </div>

          <div className="card p-6 space-y-4">
            <h3 className="text-xl font-semibold">Navigation</h3>
            <p className="text-sm text-muted-foreground">
              Navigation elements with enhanced cursor
            </p>
            <div className="space-y-2">
              <a href="#" className="nav-link block">
                Home
              </a>
              <a href="#" className="nav-link block">
                Dashboard
              </a>
              <a href="#" className="nav-link block nav-link-active">
                Convert (Active)
              </a>
            </div>
          </div>

          <div className="card p-6 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-950/20 dark:to-indigo-950/20">
            <h3 className="text-xl font-semibold mb-4">How It Works</h3>
            <ul className="space-y-2 text-sm">
              <li>• <strong>Blue ring:</strong> Hover state on interactive elements</li>
              <li>• <strong>Red ring:</strong> Click/press state</li>
              <li>• <strong>Green line:</strong> Text cursor over inputs</li>
              <li>• <strong>Gray ring:</strong> Disabled elements</li>
              <li>• <strong>Spinning ring:</strong> Loading state</li>
              <li>• <strong>Ripple effect:</strong> Click animation</li>
            </ul>
          </div>
        </div>

        <div className="text-center mt-12">
          <p className="text-sm text-muted-foreground">
            The cursor animation automatically works throughout the entire website!
          </p>
        </div>
      </div>
    </div>
  );
}
