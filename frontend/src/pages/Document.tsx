import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useEffect, useRef, useState } from "react";
import ReactQuill from "react-quill";
import "react-quill/dist/quill.snow.css";
import { useParams } from "react-router-dom";

export default function DocumentPage() {
  const { id } = useParams();
  const [content, setContent] = useState("");
  const [title, setTitle] = useState("");
  const [shareEmail, setShareEmail] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isConnected, setIsConnected] = useState(false);
  const quillRef = useRef<ReactQuill | null>(null);
  const ws = useRef<WebSocket | null>(null);
    
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      console.error('No authentication token found');
      return;
    }

    // Fetch initial document content
    const fetchDocument = async () => {
      setIsLoading(true);
      try {
        const response = await fetch(`http://localhost:8000/documents/${id}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        if (!response.ok) {
          console.error('Failed to fetch document');
          window.location.href = '/documents';
        }
        const data = await response.json();
        setContent(data.content);
        setTitle(data.title);
      } catch (error) {
        console.error('Error fetching document:', error);
      } finally {
        setIsLoading(false);
      }
    };

    // Only fetch if we're not creating a new document
    if (id !== 'new') {
      fetchDocument();
    } else {
      setIsLoading(false);
    }

    // WebSocket connection setup
    ws.current = new WebSocket(`ws://localhost:8000/ws/${id}?token=${token}`);

    ws.current.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === "update" && message.documentId === id) {
        setContent(message.content);
        if (message.title) {
          setTitle(message.title);
        }
      }
    };

    ws.current.onopen = () => {
      console.log("WebSocket connection established");
      setIsConnected(true);
    };

    ws.current.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    ws.current.onclose = () => {
      console.log("WebSocket connection closed");
      setIsConnected(false);
    };

    return () => {
      if (ws.current?.readyState === WebSocket.OPEN) {
        ws.current?.close();
      }
    };
  }, [id]);

  // Define Quill modules configuration
  const modules = {
    keyboard: {
      bindings: {
        // Remove the default space binding that might cause issues
        space: null
      }
    },
    toolbar: [
      [{ 'header': [1, 2, false] }],
      ['bold', 'italic', 'underline', 'strike', 'blockquote'],
      [{'list': 'ordered'}, {'list': 'bullet'}, {'indent': '-1'}, {'indent': '+1'}],
      ['link', 'image'],
      ['clean']
    ],
  };

  // Define formats that are allowed
  const formats = [
    'header',
    'bold', 'italic', 'underline', 'strike', 'blockquote',
    'list', 'bullet', 'indent',
    'link', 'image'
  ];

  const handleContentChange = (newContent: string) => {
    // Prevent unnecessary updates if content hasn't actually changed
    if (newContent !== content) {
      setContent(newContent);
      console.log("Sending updated content to the server");
      // Send the updated content to the server
      ws.current?.send(JSON.stringify({ 
        type: "update", 
        documentId: id, 
        content: newContent 
      }));
    }
  };

  const handleTitleChange = (newTitle: string) => {
    setTitle(newTitle);
    ws.current?.send(JSON.stringify({
      type: "update",
      documentId: id,
      content,
      title: newTitle
    }));
  };

  const handleShare = async () => {
    console.log("Sharing document with email:", shareEmail);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/documents/share`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ document_id: id, email: shareEmail })
      });
      if (!response.ok) {
        throw new Error('Failed to share document');
      }
      const data = await response.json();
      if (data.status === "success") {
        alert('Document shared successfully');
        setShareEmail("");
      } else {
        console.error(data);
        throw new Error('Failed to share document: ' + data.detail);
      }
    } catch (error) {
      console.error('Error sharing document:', error);
      alert(error);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {isLoading ? (
        <div className="flex justify-center items-center h-[700px]">
          Loading...
        </div>
      ) : (
        <>
          <div className="flex justify-between items-center mb-6">
            <div className="flex items-center space-x-4">
              <Button variant="outline" onClick={() => window.history.back()} className="mr-4">
                Back
              </Button>
              <div className="flex items-center">
                <Label className="mr-2 text-lg font-semibold">Title:</Label>
                <Input
                  type="text"
                  value={title}
                  onChange={(e) => handleTitleChange(e.target.value)}
                  className="text-2xl font-bold w-full max-w-md"
                  placeholder="Document Title"
                />
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <span className={`text-sm ${isConnected ? 'text-green-500' : 'text-red-500'}`}>
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
              <Dialog>
                <DialogTrigger asChild>
                  <Button variant="outline" className="ml-4">Share</Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle className="text-xl font-bold">Share Document</DialogTitle>
                  </DialogHeader>
                  <div className="grid gap-4 py-4">
                    <div className="grid grid-cols-4 items-center gap-4">
                      <Label htmlFor="email" className="text-right font-medium">
                        Email
                      </Label>
                      <Input
                        id="email"
                        value={shareEmail}
                        onChange={(e) => setShareEmail(e.target.value)}
                        placeholder="user@example.com"
                        className="col-span-3 border border-gray-300 rounded-md"
                      />
                    </div>
                  </div>
                  <Button onClick={handleShare} className="mt-4 bg-blue-500 text-white hover:bg-blue-600">
                    Share
                  </Button>
                </DialogContent>
              </Dialog>
            </div>
          </div>
          <ReactQuill
            ref={quillRef}
            theme="snow"
            value={content}
            onChange={handleContentChange}
            modules={modules}
            formats={formats}
            preserveWhitespace={true}
            className="h-[700px] border border-gray-300 rounded-md"
            style={{ height: '700px' }}
          />
        </>
      )}
    </div>
  );
}

