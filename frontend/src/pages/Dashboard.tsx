import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/useAuth';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTrash } from '@fortawesome/free-solid-svg-icons';

interface Document {
  id: string;
  title: string;
  lastModified: string;
  owned_by_current_user: boolean;
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
        if (response.status === 401) {
          logout();
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
        window.location.href = `/documents/${newDoc.id}`;
      }
    } catch (error) {
      console.error('Error creating document:', error);
    }
  };
  
  const handelDelete = async (id: string) => {
    const response = await fetch(`http://localhost:8000/documents/${id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });
    if (response.ok) {
      setDocuments(prev => prev.filter(doc => doc.id !== id));
    }

  }
  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-bold">My Documents</h1>
        <div className="flex gap-4">
          <button
            onClick={createNewDocument}
            className="flex items-center justify-center w-10 h-10 bg-gray-600 text-white rounded-full shadow-md hover:bg-gray-700 transition duration-300 ease-in-out transform hover:scale-105"
          >
            <span className="text-xl">+</span>
          </button>
          <button
            onClick={logout}
            className="px-4 py-2 bg-gray-600 text-white font-semibold rounded-lg shadow-md hover:bg-gray-700 transition duration-300 ease-in-out transform hover:scale-105"
          >
            Logout
          </button>
        </div>
      </div>

      {documents.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64">
          <p className="mb-4 text-lg text-gray-600">You have no documents yet.</p>
          <button
            onClick={createNewDocument}
            className="px-8 py-4 bg-blue-600 text-white font-semibold rounded-lg shadow-md hover:bg-blue-700 transition duration-300 ease-in-out transform hover:scale-105"
          >
            Create your first document
          </button>
        </div>
      ) : (
        <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
          {documents.map((doc) => (
            <div key={doc.id} className="relative p-4 border rounded-lg hover:shadow-lg transition-shadow">
              <Link to={`/documents/${doc.id}`}>
                <h2 className="font-semibold">{doc.title}</h2>
                <p className="text-sm text-gray-500">
                  Last modified: {new Date(doc.lastModified).toLocaleDateString()}
                </p>
              </Link>
              {doc.owned_by_current_user && (
                <button
                  onClick={() => handelDelete(doc.id)}
                  className="absolute top-2 right-2 text-gray-500 hover:text-gray-600"
                >
                  <FontAwesomeIcon icon={faTrash} />
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
} 