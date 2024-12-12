import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface Document {
  id: string;
  title: string;
  last_modified: string;
}

export default function Dashboard() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const { logout } = useAuth();

  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        const response = await fetch('http://localhost:8000/documents', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        });
        if (response.ok) {
          const data = await response.json();
          setDocuments(data);
        }
      } catch (error) {
        console.error('Error fetching documents:', error);
      }
    };

    fetchDocuments();
  }, []);

  const createNewDocument = async () => {
    try {
      const response = await fetch('http://localhost:8000/documents', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: 'Untitled Document',
        }),
      });
      
      if (response.ok) {
        const newDoc = await response.json();
        setDocuments(prev => [...prev, newDoc]);
        // Optionally, redirect to the new document
        window.location.href = `/doc/${newDoc.id}`;
      }
    } catch (error) {
      console.error('Error creating document:', error);
    }
  };

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-bold">My Documents</h1>
        <div className="flex gap-4">
          <button
            onClick={createNewDocument}
            className="px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90"
          >
            New Document
          </button>
          <button
            onClick={logout}
            className="px-4 py-2 bg-destructive text-destructive-foreground rounded hover:bg-destructive/90"
          >
            Logout
          </button>
        </div>
      </div>

      <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
        {documents.map((doc) => (
          <Link
            key={doc.id}
            to={`/doc/${doc.id}`}
            className="p-4 border rounded-lg hover:shadow-lg transition-shadow"
          >
            <h2 className="font-semibold">{doc.title}</h2>
            <p className="text-sm text-gray-500">
              Last modified: {new Date(doc.last_modified).toLocaleDateString()}
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
} 