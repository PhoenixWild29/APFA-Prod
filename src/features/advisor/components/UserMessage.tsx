import type { Message } from '@/types/conversation';

interface UserMessageProps {
  message: Message;
}

export default function UserMessage({ message }: UserMessageProps) {
  return (
    <div className="flex justify-end">
      <div className="max-w-[80%] rounded-2xl rounded-br-md bg-teal-700 px-4 py-2.5 text-sm text-white dark:bg-teal-600">
        <p className="whitespace-pre-wrap">{message.content}</p>
      </div>
    </div>
  );
}
