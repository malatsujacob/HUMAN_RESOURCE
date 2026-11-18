import { useCallback, useEffect, useState } from 'react'
import axios from 'axios'
import { Bell, MessageCircle, RefreshCw, Send, X } from 'lucide-react'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
const authConfig = () => ({
  headers: {
    Authorization: `Bearer ${localStorage.getItem('token') || localStorage.getItem('access_token') || ''}`,
  },
})
const formatDate = value => value ? new Date(value).toLocaleString() : ''
const formatDetail = value => typeof value === 'string' ? value : JSON.stringify(value)

export default function NotificationCenter() {
  const [notifications, setNotifications] = useState([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [open, setOpen] = useState(false)
  const [activeNotification, setActiveNotification] = useState(null)
  const [thread, setThread] = useState([])
  const [threadLoading, setThreadLoading] = useState(false)
  const [reply, setReply] = useState('')
  const [sending, setSending] = useState(false)
  const [notice, setNotice] = useState('')

  const loadNotifications = useCallback(async (nextOffset = 0, append = false) => {
    setLoading(true)
    setError('')
    try {
      const { data } = await axios.get(`${API_BASE}/notifications/mine`, {
        ...authConfig(),
        params: { offset: nextOffset, limit: 50 },
      })
      setNotifications(current => append ? [...current, ...data.items] : data.items)
      setUnreadCount(data.unread_count)
      setTotal(data.total)
      setOffset(nextOffset + data.items.length)
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'Notifications could not be loaded.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadNotifications()
    const timer = window.setInterval(() => loadNotifications(), 60000)
    return () => window.clearInterval(timer)
  }, [loadNotifications])

  const selectNotification = async item => {
    setActiveNotification(item)
    setThread([])
    setReply('')
    setNotice('')
    setError('')
    if (!item.is_read) {
      try {
        await axios.post(`${API_BASE}/notifications/${item.id}/read`, {}, authConfig())
        setNotifications(current => current.map(row => row.id === item.id ? { ...row, is_read: true } : row))
        setUnreadCount(count => Math.max(0, count - 1))
      } catch (requestError) {
        setError(requestError.response?.data?.detail || 'The notification could not be marked as read.')
      }
    }
    if (!item.can_reply) return
    setThreadLoading(true)
    try {
      const { data } = await axios.get(`${API_BASE}/notifications/${item.thread_id}/thread`, authConfig())
      setThread(data)
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'The conversation could not be loaded.')
    } finally {
      setThreadLoading(false)
    }
  }

  const sendReply = async event => {
    event.preventDefault()
    if (!activeNotification || !reply.trim()) return
    setSending(true)
    setError('')
    setNotice('')
    try {
      await axios.post(
        `${API_BASE}/notifications/${activeNotification.thread_id}/reply`,
        { message: reply.trim() },
        authConfig(),
      )
      setReply('')
      setNotice('Reply sent.')
      const { data } = await axios.get(
        `${API_BASE}/notifications/${activeNotification.thread_id}/thread`,
        authConfig(),
      )
      setThread(data)
      await loadNotifications()
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'The reply could not be sent.')
    } finally {
      setSending(false)
    }
  }

  const loadMore = () => loadNotifications(offset, true)

  return (
    <div className="notification-center">
      <button
        className="notification-center-trigger"
        type="button"
        aria-label={`Notifications${unreadCount ? `, ${unreadCount} unread` : ''}`}
        aria-expanded={open}
        aria-controls="notification-center-panel"
        onClick={() => {
          const nextOpen = !open
          setOpen(nextOpen)
          if (nextOpen) loadNotifications()
        }}
      >
        <Bell size={18} />
        <span className="notification-center-trigger-label">Notifications</span>
        {unreadCount > 0 && <span className="notification-center-count">{unreadCount > 99 ? '99+' : unreadCount}</span>}
      </button>

      {open && (
        <div className="notification-center-backdrop" onMouseDown={event => {
          if (event.target === event.currentTarget) setOpen(false)
        }}>
          <section
            id="notification-center-panel"
            className="notification-center-panel"
            role="dialog"
            aria-modal="true"
            aria-labelledby="notification-center-title"
          >
            <header className="notification-center-header">
              <div>
                <h2 id="notification-center-title">Notifications</h2>
                <p>{unreadCount} unread · {total} total</p>
              </div>
              <div className="notification-center-header-actions">
                <button type="button" className="notification-icon-button" aria-label="Refresh notifications" onClick={() => loadNotifications()}>
                  <RefreshCw size={17} />
                </button>
                <button type="button" className="notification-icon-button" aria-label="Close notifications" onClick={() => setOpen(false)}>
                  <X size={19} />
                </button>
              </div>
            </header>

            {error && <p className="notification-center-error" role="alert">{error}</p>}

            <div className="notification-center-body">
              <div className="notification-center-list" aria-label="All notifications">
                {notifications.length === 0 && !loading && <p className="notification-center-empty">No notifications yet.</p>}
                {notifications.map(item => (
                  <button
                    className={`notification-center-item${item.is_read ? '' : ' unread'}${activeNotification?.id === item.id ? ' selected' : ''}`}
                    type="button"
                    key={item.id}
                    onClick={() => selectNotification(item)}
                    aria-current={activeNotification?.id === item.id ? 'true' : undefined}
                  >
                    <span className="notification-center-item-heading">
                      <strong>{item.title || 'Notification'}</strong>
                      {!item.is_read && <span className="notification-unread-dot" aria-label="Unread" />}
                    </span>
                    <span>{item.message}</span>
                    <small>{item.sender_name} · {formatDate(item.created_at)}</small>
                  </button>
                ))}
                {offset < total && (
                  <button type="button" className="notification-load-more" onClick={loadMore} disabled={loading}>
                    {loading ? 'Loading…' : 'Load more notifications'}
                  </button>
                )}
              </div>

              <div className="notification-center-conversation">
                {!activeNotification ? (
                  <div className="notification-conversation-placeholder"><MessageCircle size={23} /><p>Select a notification to view details and replies.</p></div>
                ) : (
                  <>
                    <div className="notification-conversation-title">
                      <span className="notification-center-kicker">MESSAGE</span>
                      <h3>{activeNotification.title || 'Notification'}</h3>
                      <p>{activeNotification.message}</p>
                      <small>{activeNotification.sender_name} · {formatDate(activeNotification.created_at)}</small>
                    </div>
                    {activeNotification.details && Object.keys(activeNotification.details).length > 0 && (
                      <dl className="notification-details">
                        {Object.entries(activeNotification.details).map(([key, value]) => (
                          <div key={key}>
                            <dt>{key.replaceAll('_', ' ')}</dt>
                            <dd>{formatDetail(value)}</dd>
                          </div>
                        ))}
                      </dl>
                    )}
                    {activeNotification.can_reply ? (
                      <>
                        <div className="notification-thread" aria-live="polite">
                          {threadLoading ? <p className="notification-center-empty">Loading conversation…</p> : thread.map(message => (
                            <article className="notification-thread-message" key={message.id}>
                              <div><strong>{message.sender_name}</strong><small>{formatDate(message.created_at)}</small></div>
                              <p>{message.message}</p>
                            </article>
                          ))}
                        </div>
                        <form className="notification-reply-form" onSubmit={sendReply}>
                          <label htmlFor="notification-reply">Reply to {activeNotification.sender_name}</label>
                          <textarea
                            id="notification-reply"
                            value={reply}
                            onChange={event => setReply(event.target.value)}
                            rows="3"
                            maxLength="2000"
                            placeholder="Write a reply…"
                            required
                          />
                          {notice && <p className="notification-center-notice" role="status">{notice}</p>}
                          <button type="submit" className="notification-send-button" disabled={sending || !reply.trim()}>
                            <Send size={15} />{sending ? 'Sending…' : 'Send reply'}
                          </button>
                        </form>
                      </>
                    ) : (
                      <p className="notification-center-empty">Replies are unavailable because this notification has no identifiable sender.</p>
                    )}
                  </>
                )}
              </div>
            </div>
          </section>
        </div>
      )}
    </div>
  )
}
