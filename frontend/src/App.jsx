import React, { useState, useEffect } from 'react';
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd';
import { Calendar, User, Tag, Edit2 } from 'lucide-react';
import { v4 as uuidv4 } from 'uuid';
import { isPast, parseISO } from 'date-fns';
import './index.css';

const INITIAL_DATA = {
  lists: {
    'list-1': { id: 'list-1', title: 'To Do', cardIds: ['card-1'] },
    'list-2': { id: 'list-2', title: 'Doing', cardIds: [] },
    'list-3': { id: 'list-3', title: 'Done', cardIds: [] },
  },
  cards: {
    'card-1': {
      id: 'card-1',
      title: 'Setup Kanban Board',
      description: 'Implement drag and drop',
      tags: ['blue'],
      member: 'AR',
      dueDate: new Date().toISOString().split('T')[0]
    }
  },
  listOrder: ['list-1', 'list-2', 'list-3'],
};

const TAG_COLORS = [
  { id: 'red', label: 'Urgent' },
  { id: 'blue', label: 'Feature' },
  { id: 'green', label: 'Task' },
  { id: 'yellow', label: 'Bug' },
];

function App() {
  const [data, setData] = useState(() => {
    const saved = localStorage.getItem('kanban-data');
    return saved ? JSON.parse(saved) : INITIAL_DATA;
  });

  const [modalOpen, setModalOpen] = useState(false);
  const [editingCardId, setEditingCardId] = useState(null);
  const [activeListId, setActiveListId] = useState(null);
  
  const [formData, setFormData] = useState({
    title: '', description: '', tag: 'blue', member: '', dueDate: ''
  });

  useEffect(() => {
    localStorage.setItem('kanban-data', JSON.stringify(data));
  }, [data]);

  const onDragEnd = (result) => {
    const { destination, source, draggableId } = result;
    if (!destination) return;
    if (destination.droppableId === source.droppableId && destination.index === source.index) return;

    const startList = data.lists[source.droppableId];
    const finishList = data.lists[destination.droppableId];

    if (startList === finishList) {
      const newCardIds = Array.from(startList.cardIds);
      newCardIds.splice(source.index, 1);
      newCardIds.splice(destination.index, 0, draggableId);

      const newList = { ...startList, cardIds: newCardIds };
      setData({ ...data, lists: { ...data.lists, [newList.id]: newList } });
      return;
    }

    const startCardIds = Array.from(startList.cardIds);
    startCardIds.splice(source.index, 1);
    const newStart = { ...startList, cardIds: startCardIds };

    const finishCardIds = Array.from(finishList.cardIds);
    finishCardIds.splice(destination.index, 0, draggableId);
    const newFinish = { ...finishList, cardIds: finishCardIds };

    setData({
      ...data,
      lists: { ...data.lists, [newStart.id]: newStart, [newFinish.id]: newFinish }
    });
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

  const saveCard = () => {
    if (!formData.title.trim()) return;

    if (editingCardId) {
      setData(prev => ({
        ...prev,
        cards: {
          ...prev.cards,
          [editingCardId]: {
            ...prev.cards[editingCardId],
            title: formData.title,
            description: formData.description,
            tags: [formData.tag],
            member: formData.member,
            dueDate: formData.dueDate
          }
        }
      }));
    } else {
      const newCardId = uuidv4();
      const newCard = {
        id: newCardId,
        title: formData.title,
        description: formData.description,
        tags: [formData.tag],
        member: formData.member,
        dueDate: formData.dueDate
      };
      
      const list = data.lists[activeListId];
      setData(prev => ({
        ...prev,
        cards: { ...prev.cards, [newCardId]: newCard },
        lists: {
          ...prev.lists,
          [list.id]: { ...list, cardIds: [...list.cardIds, newCardId] }
        }
      }));
    }
    setModalOpen(false);
  };

  return (
    <div className="board-container">
      <div className="board-header">Forge 2 Qualifier - Kanban</div>
      <DragDropContext onDragEnd={onDragEnd}>
        <div className="board-content">
          {data.listOrder.map(listId => {
            const list = data.lists[listId];
            const cards = list.cardIds.map(taskId => data.cards[taskId]);

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
                                    {card.tags.map(tag => (
                                      <span key={tag} className={`tag tag-${tag}`}>
                                        {TAG_COLORS.find(t => t.id === tag)?.label}
                                      </span>
                                    ))}
                                  </div>
                                  <Edit2 size={14} style={{cursor:'pointer', color:'#5e6c84'}} onClick={() => openModal(list.id, card.id)} />
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
