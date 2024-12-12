import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface DocumentData {
  documentId: string;
  content: string;
  title: string;
  lastModified: string;
}

export default function Document() {
  const { id } = useParams<{ id: string }>();
  const [document, setDocument] = useState<DocumentData | null>(null);
  const [content, setContent] = useState('');
  const [title, setTitle] = useState('');
  const navigate = useNavigate();
  const { user } = useAuth();

  useEffect(() => {
    const fetchDocument = async () => {
      if (id === 'new') {
        setDocument({
          documentId: '',
          content: '',
          title: 'Untitled Document',
          lastModified: new Date().toISOString(),
        });
        setTitle('Untitled Document');
        return;
      }

      try {
        const response = await fetch(`http://localhost:8000/documents/${id}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        });
        if (response.ok) {
          const data = await response.json();
          setDocument(data);
          setContent(data.content);
          setTitle(data.title);
        }
      } catch (error) {
        console.error('Error fetching document:', error);
      }
    };

    fetchDocument();
  }, [id]);

  const handleSave = async () => {
    try {
      const method = id === 'new' ? 'POST' : 'PUT';
      const url = id === 'new' 
        ? 'http://localhost:8000/documents'
        : `http://localhost:8000/documents/${id}`;

      const response = await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          content, 
          title,
          owner_id: user?.id 
        }),
      });

      if (response.ok && id === 'new') {
        const data = await response.json();
        navigate(`/doc/${data.id}`);
      }
    } catch (error) {
      console.error('Error saving document:', error);
    }
  };

  if (!document) {
    return <div>Loading...</div>;
  }

  return (
    <div className="min-h-screen p-4">
      <div className="max-w-4xl mx-auto space-y-4">
        <div className="flex justify-between items-center">
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="text-2xl font-bold px-2 py-1 border rounded flex-1 mr-4"
          />
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-black text-white rounded hover:bg-black/90"
          >
            Save
          </button>
        </div>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          className="w-full h-[calc(100vh-200px)] p-4 border rounded"
        />
      </div>
    </div>
  );
}

