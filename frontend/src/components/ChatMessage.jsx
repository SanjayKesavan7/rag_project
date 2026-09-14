import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

function ChatMessage({ role, content }) {
  const isAssistant = role === 'assistant';
  
  return (
    <div className={`message-row ${role}`}>
      <div className={`message-bubble ${role}`}>
        <div className="role-label">{isAssistant ? 'ChefRAG' : 'You'}</div>
        {isAssistant ? (
          <div className="markdown-body">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {content}
            </ReactMarkdown>
          </div>
        ) : (
          <p style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{content}</p>
        )}
      </div>
    </div>
  );
}

export default ChatMessage;
