/**
 * Task Cancellation Component
 * 
 * Allows administrators to:
 * - View running tasks
 * - Cancel specific tasks
 * - Bulk task management
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface RunningTask {
  task_id: string;
  task_name: string;
  started_at: string;
  worker: string;
  progress: number;
}

export const TaskCanceller: React.FC = () => {
  const [tasks, setTasks] = useState<RunningTask[]>([]);
  const [selectedTasks, setSelectedTasks] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetchRunningTasks();
    const interval = setInterval(fetchRunningTasks, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchRunningTasks = async () => {
    try {
      const response = await axios.get('/admin/jobs/running');
      setTasks(response.data.tasks || []);
    } catch (error) {
      console.error('Failed to fetch running tasks:', error);
    }
  };

  const handleCancelTask = async (taskId: string) => {
    if (!confirm(`Cancel task ${taskId}?`)) return;

    try {
      await axios.delete(`/admin/jobs/cancel/${taskId}`);
      alert('Task cancelled successfully');
      fetchRunningTasks();
    } catch (error) {
      alert('Cancellation failed: ' + error.message);
    }
  };

  const handleBulkCancel = async () => {
    if (selectedTasks.size === 0) {
      alert('No tasks selected');
      return;
    }

    if (!confirm(`Cancel ${selectedTasks.size} selected tasks?`)) return;

    try {
      await axios.post('/admin/jobs/bulk-cancel', {
        task_ids: Array.from(selectedTasks)
      });
      alert('Tasks cancelled successfully');
      setSelectedTasks(new Set());
      fetchRunningTasks();
    } catch (error) {
      alert('Bulk cancellation failed: ' + error.message);
    }
  };

  return (
    <div className="task-canceller">
      <h2>Task Management</h2>
      
      {selectedTasks.size > 0 && (
        <div className="bulk-actions">
          <span>{selectedTasks.size} tasks selected</span>
          <button onClick={handleBulkCancel} className="btn-danger">
            Cancel Selected
          </button>
        </div>
      )}

      <table className="tasks-table">
        <thead>
          <tr>
            <th>
              <input
                type="checkbox"
                onChange={(e) => {
                  if (e.target.checked) {
                    setSelectedTasks(new Set(tasks.map(t => t.task_id)));
                  } else {
                    setSelectedTasks(new Set());
                  }
                }}
              />
            </th>
            <th>Task ID</th>
            <th>Task Name</th>
            <th>Worker</th>
            <th>Started</th>
            <th>Progress</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {tasks.map((task) => (
            <tr key={task.task_id}>
              <td>
                <input
                  type="checkbox"
                  checked={selectedTasks.has(task.task_id)}
                  onChange={(e) => {
                    const newSelected = new Set(selectedTasks);
                    if (e.target.checked) {
                      newSelected.add(task.task_id);
                    } else {
                      newSelected.delete(task.task_id);
                    }
                    setSelectedTasks(newSelected);
                  }}
                />
              </td>
              <td>{task.task_id.substring(0, 8)}...</td>
              <td>{task.task_name}</td>
              <td>{task.worker}</td>
              <td>{new Date(task.started_at).toLocaleTimeString()}</td>
              <td>{task.progress}%</td>
              <td>
                <button
                  onClick={() => handleCancelTask(task.task_id)}
                  className="btn-sm btn-danger"
                >
                  Cancel
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {tasks.length === 0 && (
        <div className="no-tasks">No running tasks</div>
      )}
    </div>
  );
};

