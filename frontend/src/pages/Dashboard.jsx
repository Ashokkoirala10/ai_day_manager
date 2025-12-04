import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { routineAPI } from '../services/api';
import ChatAI from './ChatAI';


const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [routines, setRoutines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    time: '',
    repeat_type: 'once',
  });
  const [editingId, setEditingId] = useState(null);

  useEffect(() => {
    fetchRoutines();
  }, []);

  const fetchRoutines = async () => {
    try {
      const response = await routineAPI.getAll();
      setRoutines(response.data.results || response.data);
    } catch (error) {
      console.error('Error fetching routines:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      console.log('Sending data:', formData);
      
      if (editingId) {
        await routineAPI.update(editingId, formData);
      } else {
        await routineAPI.create(formData);
      }
      fetchRoutines();
      resetForm();
    } catch (error) {
      console.error('Error saving routine:', error);
      console.error('Error response:', error.response?.data);
    }
  };

  const handleEdit = (routine) => {
    setFormData({
      title: routine.title,
      time: routine.time,
      repeat_type: routine.repeat_type,
    });
    setEditingId(routine.id);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this routine?')) {
      try {
        await routineAPI.delete(id);
        fetchRoutines();
      } catch (error) {
        console.error('Error deleting routine:', error);
      }
    }
  };

  const handleToggle = async (id) => {
    try {
      await routineAPI.toggle(id);
      fetchRoutines();
    } catch (error) {
      console.error('Error toggling routine:', error);
    }
  };

  const resetForm = () => {
    setFormData({ title: '', time: '', repeat_type: 'once' });
    setEditingId(null);
    setShowForm(false);
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  if (loading) {
    return <div style={styles.loading}>Loading...</div>;
  }

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <div>
          <h1 style={styles.headerTitle}>My Routines</h1>
          <p style={styles.headerSubtitle}>Welcome, {user?.username}!</p>
        </div>
        <button onClick={handleLogout} style={styles.logoutBtn}>
          Logout
        </button>
      </header>

      <div style={styles.content}>
        <div style={styles.actions}>
          <button 
            onClick={() => setShowForm(!showForm)} 
            style={styles.addBtn}
          >
            {showForm ? 'Cancel' : '+ Add Routine'}
          </button>
        </div>
     

        {showForm && (
          <div style={styles.formCard}>
            <h3 style={styles.formTitle}>
              {editingId ? 'Edit Routine' : 'New Routine'}
            </h3>
            <form onSubmit={handleSubmit} style={styles.form}>
              <div style={styles.formGroup}>
                <label style={styles.label}>Title</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  required
                  style={styles.input}
                  placeholder="Enter routine title"
                />
              </div>
              

              <div style={styles.formRow}>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Time</label>
                  <input
                    type="time"
                    value={formData.time}
                    onChange={(e) => setFormData({ ...formData, time: e.target.value })}
                    required
                    style={styles.input}
                  />
                </div>

                <div style={styles.formGroup}>
                  <label style={styles.label}>Repeat</label>
                  <select
                    value={formData.repeat_type}
                    onChange={(e) => setFormData({ ...formData, repeat_type: e.target.value })}
                    style={styles.select}
                  >
                    <option value="once">Once</option>
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                  </select>
                </div>
              </div>

              <div style={styles.formActions}>
                <button type="submit" style={styles.submitBtn}>
                  {editingId ? 'Update' : 'Create'}
                </button>
                <button type="button" onClick={resetForm} style={styles.cancelBtn}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        <div style={styles.routinesList}>
          {routines.length === 0 ? (
            <div style={styles.empty}>
              <p>No routines yet. Create your first routine!</p>
            </div>
          ) : (
            routines.map((routine) => (
              <div key={routine.id} style={styles.routineCard}>
                <div style={styles.routineHeader}>
                 
                  <div style={styles.routineInfo}>
                    <h3 style={{
                      ...styles.routineTitle,
                      textDecoration: routine.is_completed ? 'line-through' : 'none',
                      opacity: routine.is_completed ? 0.6 : 1,
                    }}>
                      {routine.title}
                    </h3>
                    <div style={styles.routineMeta}>
                      <span>🕐 {routine.time}</span>
                      <span style={styles.badge}>{routine.repeat_type}</span>
                    </div>
                  </div>
                </div>
                <div style={styles.routineActions}>
                  <button 
                    onClick={() => handleEdit(routine)} 
                    style={styles.editBtn}
                  >
                    Edit
                  </button>
                  <button 
                    onClick={() => handleDelete(routine.id)} 
                    style={styles.deleteBtn}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* ChatAI Component - Floating chat button */}
      <ChatAI/>
    </div>
    
  );
};

const styles = {
  container: {
    minHeight: '100vh',
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: 'white',
    padding: '20px 40px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerTitle: {
    margin: 0,
    color: '#333',
  },
  headerSubtitle: {
    margin: '5px 0 0 0',
    color: '#666',
    fontSize: '14px',
  },
  logoutBtn: {
    padding: '8px 16px',
    backgroundColor: '#dc3545',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  content: {
    maxWidth: '900px',
    margin: '0 auto',
    padding: '40px 20px',
  },
  actions: {
    marginBottom: '20px',
  },
  addBtn: {
    padding: '12px 24px',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '16px',
    fontWeight: '500',
  },
  formCard: {
    backgroundColor: 'white',
    padding: '30px',
    borderRadius: '8px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
    marginBottom: '30px',
  },
  formTitle: {
    marginTop: 0,
    marginBottom: '20px',
    color: '#333',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
  },
  formGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: '5px',
    flex: 1,
  },
  formRow: {
    display: 'flex',
    gap: '20px',
  },
  label: {
    fontSize: '14px',
    fontWeight: '500',
    color: '#555',
  },
  input: {
    padding: '10px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '14px',
  },
  select: {
    padding: '10px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '14px',
    backgroundColor: 'white',
  },
  formActions: {
    display: 'flex',
    gap: '10px',
  },
  submitBtn: {
    padding: '10px 20px',
    backgroundColor: '#28a745',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
  },
  cancelBtn: {
    padding: '10px 20px',
    backgroundColor: '#6c757d',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
  },
  routinesList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '15px',
  },
  routineCard: {
    backgroundColor: 'white',
    padding: '20px',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  routineHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '15px',
    flex: 1,
  },
  checkbox: {
    width: '20px',
    height: '20px',
    cursor: 'pointer',
  },
  routineInfo: {
    flex: 1,
  },
  routineTitle: {
    margin: '0 0 8px 0',
    color: '#333',
  },
  routineMeta: {
    display: 'flex',
    gap: '15px',
    fontSize: '14px',
    color: '#666',
  },
  badge: {
    backgroundColor: '#e9ecef',
    padding: '2px 8px',
    borderRadius: '12px',
    fontSize: '12px',
    textTransform: 'capitalize',
  },
  routineActions: {
    display: 'flex',
    gap: '10px',
  },
  editBtn: {
    padding: '6px 12px',
    backgroundColor: '#ffc107',
    color: '#333',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
  },
  deleteBtn: {
    padding: '6px 12px',
    backgroundColor: '#dc3545',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
  },
  empty: {
    textAlign: 'center',
    padding: '60px 20px',
    color: '#999',
  },
  loading: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '100vh',
    fontSize: '20px',
    color: '#666',
  },
};

export default Dashboard;