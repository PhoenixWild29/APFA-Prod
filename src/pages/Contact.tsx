import { Button } from '@/components/ui/button';

export default function Contact() {
  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-3xl font-bold">Contact Us</h1>

      <div className="rounded-lg border bg-card p-6">
        <form className="space-y-6">
          <div>
            <label htmlFor="name" className="mb-2 block text-sm font-medium">
              Name
            </label>
            <input
              type="text"
              id="name"
              className="w-full rounded-md border bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder="Your name"
            />
          </div>

          <div>
            <label htmlFor="email" className="mb-2 block text-sm font-medium">
              Email
            </label>
            <input
              type="email"
              id="email"
              className="w-full rounded-md border bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder="your.email@example.com"
            />
          </div>

          <div>
            <label htmlFor="message" className="mb-2 block text-sm font-medium">
              Message
            </label>
            <textarea
              id="message"
              rows={5}
              className="w-full rounded-md border bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder="How can we help you?"
            />
          </div>

          <Button type="submit" className="w-full">
            Send Message
          </Button>
        </form>
      </div>

      <div className="space-y-4 text-muted-foreground">
        <h2 className="text-xl font-semibold text-foreground">Other Ways to Reach Us</h2>
        <div className="space-y-2">
          <p>
            <strong>Email:</strong> support@apfa.io
          </p>
          <p>
            <strong>Slack:</strong> #apfa-support
          </p>
          <p>
            <strong>GitHub:</strong> github.com/apfa/apfa-prod
          </p>
        </div>
      </div>
    </div>
  );
}

