import React, { useState, useEffect } from 'react';
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd';
import { Calendar, User, Tag, Edit2, Trash2 } from 'lucide-react';
import { v4 as uuidv4 } from 'uuid';
import { isPast, parseISO } from 'date-fns';
import './index.css';

const API_URL = 'http://localhost:3001/tasks';

const LISTS = {
  'list-1': { id: 'list-1', title: 'To Do' },
  'list-2': { id: 'list-2', title: 'Doing' },
  'list-3': { id: 'list-3', title: 'Done' }
};

const LIST_ORDER = ['list-1', 'list-2', 'list-3'];

const TAG_COLORS = [
  { id: 'red', label: 'Urgent' },
  { id: 'blue', label: 'Feature' },
  { id: 'green', label: 'Task' },
  { id: 'yellow', label: 'Bug' },
];

function App() {
  const [data, setData] = useState({
    lists: {
      'list-1': { ...LISTS['list-1'], cardIds: [] },
      'list-2': { ...LISTS['list-2'], cardIds: [] },
      'list-3': { ...LISTS['list-3'], cardIds: [] },
    },
    cards: {},
    listOrder: LIST_ORDER,
  });

  const [modalOpen, setModalOpen] = useState(false);
  const [editingCardId, setEditingCardId] = useState(null);
  const [activeListId, setActiveListId] = useState(null);
  
  const [formData, setFormData] = useState({
    title: '', description: '', tag: 'blue', member: '', dueDate: ''
  });

  const fetchTasks = async () => {
    try {
      const res = await fetch(API_URL);
      const tasks = await res.json();
      
      const newCards = {};
      const newLists = {
        'list-1': { ...LISTS['list-1'], cardIds: [] },
        'list-2': { ...LISTS['list-2'], cardIds: [] },
        'list-3': { ...LISTS['list-3'], cardIds: [] },
      };

      tasks.forEach(t => {
        let listId = 'list-1';
        if (t.status === 'Doing') listId = 'list-2';
        if (t.status === 'Done') listId = 'list-3';

        // Parse description if it's JSON to get tags/members, otherwise basic string
        let desc = t.description;
        let tags = ['blue'];
        let member = '';
        let dueDate = '';
        
        try {
          if (t.description && t.description.startsWith('{')) {
            const parsed = JSON.parse(t.description);
            desc = parsed.text || '';
            tags = parsed.tags || ['blue'];
            member = parsed.member || '';
            dueDate = parsed.dueDate || '';
          }
        } catch (e) {}

        newCards[t.id] = {
          id: t.id,
          title: t.title,
          description: desc,
          tags,
          member,
          dueDate
        };
        newLists[listId].cardIds.push(t.id);
      });

      setData({
        lists: newLists,
        cards: newCards,
        listOrder: LIST_ORDER
      });
    } catch (err) {
      console.error('Failed to fetch tasks', err);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  const onDragEnd = async (result) => {
    const { destination, source, draggableId } = result;
    if (!destination) return;
    if (destination.droppableId === source.droppableId && destination.index === source.index) return;

    const startList = data.lists[source.droppableId];
    const finishList = data.lists[destination.droppableId];

    // Optimistic UI update
    let newData = { ...data };
    
    if (startList === finishList) {
      const newCardIds = Array.from(startList.cardIds);
      newCardIds.splice(source.index, 1);
      newCardIds.splice(destination.index, 0, draggableId);

      const newList = { ...startList, cardIds: newCardIds };
      newData = { ...data, lists: { ...data.lists, [newList.id]: newList } };
      setData(newData);
    } else {
      const startCardIds = Array.from(startList.cardIds);
      startCardIds.splice(source.index, 1);
      const newStart = { ...startList, cardIds: startCardIds };

      const finishCardIds = Array.from(finishList.cardIds);
      finishCardIds.splice(destination.index, 0, draggableId);
      const newFinish = { ...finishList, cardIds: finishCardIds };

      newData = {
        ...data,
        lists: { ...data.lists, [newStart.id]: newStart, [newFinish.id]: newFinish }
      };
      setData(newData);

      // Save to backend if changing status
      try {
        await fetch(`${API_URL}/${draggableId}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status: finishList.title })
        });
      } catch (err) {
        console.error('Failed to update task status', err);
        fetchTasks(); // rollback on error
      }
    }
  };

  const openModal = (listId, cardId = null) => {
    setActiveListId(listId);
    setEditingCardId(cardId);
    if (cardId) {
      const card = data.cards[cardId];
      setFormData({
        title: card.title,
        description: card.description || '',
        tag: card.tags[0] || 'blue',
        member: card.member || '',
        dueDate: card.dueDate || ''
      });
    } else {
      setFormData({ title: '', description: '', tag: 'blue', member: '', dueDate: '' });
    }
    setModalOpen(true);
  };

  const saveCard = async () => {
    if (!formData.title.trim()) return;

    const list = data.lists[activeListId];
    const status = list.title;
    const fullDesc = JSON.stringify({
      text: formData.description,
      tags: [formData.tag],
      member: formData.member,
      dueDate: formData.dueDate
    });

    try {
      if (editingCardId) {
        await fetch(`${API_URL}/${editingCardId}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title: formData.title, status, description: fullDesc })
        });
      } else {
        const newCardId = uuidv4();
        await fetch(API_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id: newCardId, title: formData.title, status, description: fullDesc })
        });
      }
      setModalOpen(false);
      fetchTasks();
    } catch (err) {
      console.error('Failed to save card', err);
    }
  };

  const deleteCard = async (cardId) => {
    try {
      await fetch(`${API_URL}/${cardId}`, { method: 'DELETE' });
      fetchTasks();
    } catch (err) {
      console.error('Failed to delete card', err);
    }
  };

  return (
    <div className="board-container">
      <div className="board-header">Forge 2 Qualifier - Kanban</div>
      <DragDropContext onDragEnd={onDragEnd}>
        <div className="board-content">
          {data.listOrder.map(listId => {
            const list = data.lists[listId];
            const cards = list.cardIds.map(taskId => data.cards[taskId]).filter(Boolean);

            return (
              <div key={list.id} className="list">
                <div className="list-header">{list.title}</div>
                <Droppable droppableId={list.id}>
                  {(provided) => (
                    <div className="card-list" ref={provided.innerRef} {...provided.droppableProps}>
                      {cards.map((card, index) => (
                        <Draggable key={card.id} draggableId={card.id} index={index}>
                          {(provided) => {
                            const isOverdue = card.dueDate && isPast(parseISO(card.dueDate)) && card.dueDate !== new Date().toISOString().split('T')[0];
                            return (
                              <div
                                className="card"
                                ref={provided.innerRef}
                                {...provided.draggableProps}
                                {...provided.dragHandleProps}
                              >
                                <div style={{display: 'flex', justifyContent: 'space-between'}}>
                                  <div className="card-tags">
                                    {card.tags && card.tags.map(tag => (
                                      <span key={tag} className={`tag tag-${tag}`}>
                                        {TAG_COLORS.find(t => t.id === tag)?.label}
                                      </span>
                                    ))}
                                  </div>
                                  <div style={{display:'flex', gap:'8px'}}>
                                    <Edit2 size={14} style={{cursor:'pointer', color:'#5e6c84'}} onClick={() => openModal(list.id, card.id)} />
                                    <Trash2 size={14} style={{cursor:'pointer', color:'#ff5630'}} onClick={() => deleteCard(card.id)} />
                                  </div>
                                </div>
                                <div className="card-title">{card.title}</div>
                                {card.description && <div style={{fontSize: 12, color: '#5e6c84', marginBottom: 8}}>{card.description}</div>}
                                
                                <div className="card-footer">
                                  {card.dueDate && (
                                    <div className={`due-date ${isOverdue ? 'overdue' : ''}`}>
                                      <Calendar size={12} /> {card.dueDate}
                                    </div>
                                  )}
                                  {card.member && (
                                    <div className="member" title={card.member}>{card.member.substring(0, 2).toUpperCase()}</div>
                                  )}
                                </div>
                              </div>
                            );
                          }}
                        </Draggable>
                      ))}
                      {provided.placeholder}
                    </div>
                  )}
                </Droppable>
                <div className="add-card-btn" onClick={() => openModal(list.id)}>+ Add a card</div>
              </div>
            );
          })}
        </div>
      </DragDropContext>

      {modalOpen && (
        <div className="modal-overlay">
          <div className="modal">
            <h2>{editingCardId ? 'Edit Card' : 'New Card'}</h2>
            <div className="form-group">
              <label>Title</label>
              <input value={formData.title} onChange={e => setFormData({...formData, title: e.target.value})} autoFocus />
            </div>
            <div className="form-group">
              <label>Description</label>
              <textarea value={formData.description} onChange={e => setFormData({...formData, description: e.target.value})} />
            </div>
            <div className="form-group">
              <label>Tag</label>
              <select value={formData.tag} onChange={e => setFormData({...formData, tag: e.target.value})}>
                {TAG_COLORS.map(t => <option key={t.id} value={t.id}>{t.label}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>Member Initials (e.g. AR)</label>
              <input value={formData.member} maxLength={2} onChange={e => setFormData({...formData, member: e.target.value})} />
            </div>
            <div className="form-group">
              <label>Due Date</label>
              <input type="date" value={formData.dueDate} onChange={e => setFormData({...formData, dueDate: e.target.value})} />
            </div>
            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => setModalOpen(false)}>Cancel</button>
              <button className="btn-primary" onClick={saveCard}>Save</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
