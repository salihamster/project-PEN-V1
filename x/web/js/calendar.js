// ========================================
// CALENDAR - CALENDAR PAGE MANAGEMENT
// ========================================

import { renderMarkup } from './utils.js';

let currentDate = new Date();
let calendarEvents = {};

const MONTHS_TR = [
    'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
    'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'
];

// ========================================
// INITIALIZATION
// ========================================

export function setupCalendar() {
    const calendarBtn = document.getElementById('calendarBtn');
    const calendarBackBtn = document.getElementById('calendarBackBtn');
    const calendarTodayBtn = document.getElementById('calendarTodayBtn');
    const calendarPrevBtn = document.getElementById('calendarPrevBtn');
    const calendarNextBtn = document.getElementById('calendarNextBtn');
    const calendarDayBackBtn = document.getElementById('calendarDayBackBtn');
    const calendarEventBackBtn = document.getElementById('calendarEventBackBtn');

    // Open Calendar
    if (calendarBtn) {
        calendarBtn.addEventListener('click', openCalendar);
    }

    // Day Panel Back Button
    if (calendarDayBackBtn) {
        calendarDayBackBtn.addEventListener('click', closeDayPanel);
    }

    // Event Panel Back Button
    if (calendarEventBackBtn) {
        calendarEventBackBtn.addEventListener('click', closeEventDetail);
    }

    // Close Calendar
    if (calendarBackBtn) {
        calendarBackBtn.addEventListener('click', closeCalendar);
    }

    // Today Button
    if (calendarTodayBtn) {
        calendarTodayBtn.addEventListener('click', () => {
            currentDate = new Date();
            renderCalendar();
        });
    }

    // Navigation
    if (calendarPrevBtn) {
        calendarPrevBtn.addEventListener('click', () => {
            currentDate.setMonth(currentDate.getMonth() - 1);
            renderCalendar();
        });
    }

    if (calendarNextBtn) {
        calendarNextBtn.addEventListener('click', () => {
            currentDate.setMonth(currentDate.getMonth() + 1);
            renderCalendar();
        });
    }

    console.log('Calendar initialized');
}

// ========================================
// PAGE NAVIGATION
// ========================================

async function openCalendar() {
    const calendarPage = document.getElementById('calendarPage');
    const appContainer = document.querySelector('.app');

    if (calendarPage) {
        calendarPage.classList.add('open');
        if (appContainer) {
            appContainer.classList.add('calendar-open');
        }

        // Load calendar data and render
        await loadCalendarData();
        renderCalendar();
    }
}

function closeCalendar() {
    const calendarPage = document.getElementById('calendarPage');
    const appContainer = document.querySelector('.app');

    if (calendarPage) {
        calendarPage.classList.remove('open');
        if (appContainer) {
            appContainer.classList.remove('calendar-open');
        }
    }
}

// ========================================
// CALENDAR RENDERING
// ========================================

async function loadCalendarData() {
    try {
        console.log('Loading calendar data...');
        const response = await fetch('/api/pen/calendar/events');
        const data = await response.json();

        console.log('Calendar API response:', data);

        if (data.status === 'success') {
            calendarEvents = data.events || {};
            console.log('Calendar events loaded:', Object.keys(calendarEvents).length, 'dates');
        } else {
            console.error('Calendar API error:', data.error);
        }
    } catch (error) {
        console.error('Failed to load calendar data:', error);
    }
}

function renderCalendar() {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();

    // Update month display
    const monthDisplay = document.getElementById('calendarCurrentMonth');
    if (monthDisplay) {
        monthDisplay.textContent = `${MONTHS_TR[month]} ${year}`;
    }

    // Get first day of month and number of days
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();

    // Get day of week (0 = Sunday, adjust to Monday = 0)
    let startDay = firstDay.getDay() - 1;
    if (startDay === -1) startDay = 6; // Sunday becomes 6

    // Get previous month days
    const prevMonth = new Date(year, month, 0);
    const daysInPrevMonth = prevMonth.getDate();

    // Build calendar grid
    const calendarGrid = document.getElementById('calendarGrid');
    if (!calendarGrid) return;

    calendarGrid.innerHTML = '';

    // Previous month days
    for (let i = startDay - 1; i >= 0; i--) {
        const day = daysInPrevMonth - i;
        const cell = createDayCell(day, true, year, month - 1);
        calendarGrid.appendChild(cell);
    }

    // Current month days
    const today = new Date();
    for (let day = 1; day <= daysInMonth; day++) {
        const isToday = (
            day === today.getDate() &&
            month === today.getMonth() &&
            year === today.getFullYear()
        );
        const cell = createDayCell(day, false, year, month, isToday);
        calendarGrid.appendChild(cell);
    }

    // Next month days
    const remainingCells = 42 - (startDay + daysInMonth); // 6 rows * 7 days
    for (let day = 1; day <= remainingCells; day++) {
        const cell = createDayCell(day, true, year, month + 1);
        calendarGrid.appendChild(cell);
    }
}

function createDayCell(day, isOtherMonth, year, month, isToday = false) {
    const cell = document.createElement('div');
    cell.className = 'calendar-day';

    if (isOtherMonth) {
        cell.classList.add('other-month');
    }

    if (isToday) {
        cell.classList.add('today');
    }

    // Day number
    const dayNumber = document.createElement('div');
    dayNumber.className = 'calendar-day-number';
    dayNumber.textContent = day;
    cell.appendChild(dayNumber);

    // Events container
    const eventsContainer = document.createElement('div');
    eventsContainer.className = 'calendar-day-events';

    // Check for events on this day
    const dateKey = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    const dayEvents = calendarEvents[dateKey] || [];

    if (dayEvents.length > 0) {
        cell.classList.add('has-events');

        // Show up to 3 event dots
        const visibleEvents = dayEvents.slice(0, 3);
        visibleEvents.forEach(event => {
            const dot = document.createElement('div');
            dot.className = `calendar-event-dot ${event.type || 'fixed'}`;
            dot.title = event.title;
            eventsContainer.appendChild(dot);
        });

        // Show count if more than 3
        if (dayEvents.length > 3) {
            const count = document.createElement('div');
            count.className = 'calendar-event-count';
            count.textContent = `+${dayEvents.length - 3}`;
            eventsContainer.appendChild(count);
        }
    }

    cell.appendChild(eventsContainer);

    // Click handler
    if (!isOtherMonth) {
        cell.addEventListener('click', () => {
            showDayDetails(dateKey, dayEvents);
        });
    }

    return cell;
}

function showDayDetails(dateKey, events) {
    // Open day details panel
    const layout = document.querySelector('.calendar-layout');
    if (layout) {
        layout.classList.add('day-panel-open');
    }

    // Format date nicely
    const [year, month, day] = dateKey.split('-');
    const date = new Date(year, parseInt(month) - 1, parseInt(day));
    const dateStr = date.toLocaleDateString('tr-TR', {
        weekday: 'long',
        day: 'numeric',
        month: 'long',
        year: 'numeric'
    });

    // Render day details
    renderDayDetails(dateKey, dateStr, events);
}

function renderDayDetails(dateKey, dateStr, events) {
    const panel = document.getElementById('calendarDayPanel');
    const content = document.getElementById('calendarDayContent');
    
    if (!panel || !content) return;

    // Update header
    const dateTitle = document.getElementById('calendarDayDate');
    if (dateTitle) {
        dateTitle.textContent = dateStr;
    }

    // Render events
    if (events.length === 0) {
        content.innerHTML = `
            <div class="calendar-day-empty">
                <i class="fas fa-calendar-check"></i>
                <p>Bu günde etkinlik yok</p>
            </div>
        `;
        return;
    }

    // Sort events by time
    const sortedEvents = events.sort((a, b) => {
        const timeA = a.start_date || a.window_start || '';
        const timeB = b.start_date || b.window_start || '';
        return timeA.localeCompare(timeB);
    });

    const html = sortedEvents.map(event => {
        const time = event.start_date ? new Date(event.start_date).toLocaleTimeString('tr-TR', {
            hour: '2-digit',
            minute: '2-digit'
        }) : 'Esnek';

        const statusClass = event.type === 'fixed' ? 'fixed' : 'flexible';
        const statusText = event.type === 'fixed' ? 'Sabit' : 'Esnek';

        return `
            <div class="calendar-event-item" data-event-id="${event.id}">
                <div class="calendar-event-time">
                    <span class="event-time-text">${time}</span>
                    <span class="event-type-badge ${statusClass}">${statusText}</span>
                </div>
                <div class="calendar-event-info">
                    <h4 class="calendar-event-title">${escapeHtml(event.title)}</h4>
                    ${event.description ? `<p class="calendar-event-desc">${escapeHtml(event.description.substring(0, 80))}...</p>` : ''}
                </div>
                <i class="fas fa-chevron-right calendar-event-arrow"></i>
            </div>
        `;
    }).join('');

    content.innerHTML = html;

    // Add click handlers
    document.querySelectorAll('.calendar-event-item').forEach(item => {
        item.addEventListener('click', () => {
            const eventId = item.dataset.eventId;
            const event = events.find(e => e.id === eventId);
            if (event) {
                showEventDetails(event);
            }
        });
    });
}

function showEventDetails(event) {
    const layout = document.querySelector('.calendar-layout');
    if (layout) {
        layout.classList.add('event-detail-open');
    }

    const panel = document.getElementById('calendarEventPanel');
    const content = document.getElementById('calendarEventContent');
    
    if (!panel || !content) return;

    // Format date and time
    let dateTimeStr = '';
    if (event.start_date) {
        const date = new Date(event.start_date);
        dateTimeStr = date.toLocaleString('tr-TR', {
            weekday: 'long',
            day: 'numeric',
            month: 'long',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } else if (event.window_start && event.window_end) {
        const start = new Date(event.window_start);
        const end = new Date(event.window_end);
        dateTimeStr = `${start.toLocaleDateString('tr-TR')} - ${end.toLocaleDateString('tr-TR')}`;
    }

    const statusClass = event.type === 'fixed' ? 'fixed' : 'flexible';
    const statusText = event.type === 'fixed' ? 'Sabit Etkinlik' : 'Esnek Etkinlik';

    content.innerHTML = `
        <div class="event-detail-header">
            <h2 class="event-detail-title">${escapeHtml(event.title)}</h2>
            <span class="event-type-badge ${statusClass}">${statusText}</span>
        </div>
        
        <div class="event-detail-section">
            <div class="event-detail-label">
                <i class="fas fa-clock"></i>
                <span>Zaman</span>
            </div>
            <div class="event-detail-value">${dateTimeStr}</div>
        </div>

        ${event.description ? `
        <div class="event-detail-section">
            <div class="event-detail-label">
                <i class="fas fa-align-left"></i>
                <span>Açıklama</span>
            </div>
            <div class="event-detail-value">${escapeHtml(event.description)}</div>
        </div>
        ` : ''}

        ${event.tags && event.tags.length > 0 ? `
        <div class="event-detail-section">
            <div class="event-detail-label">
                <i class="fas fa-tags"></i>
                <span>Etiketler</span>
            </div>
            <div class="event-detail-tags">
                ${event.tags.map(tag => `<span class="event-tag">${escapeHtml(tag)}</span>`).join('')}
            </div>
        </div>
        ` : ''}

        ${event.duration_minutes ? `
        <div class="event-detail-section">
            <div class="event-detail-label">
                <i class="fas fa-hourglass-half"></i>
                <span>Süre</span>
            </div>
            <div class="event-detail-value">${event.duration_minutes} dakika</div>
        </div>
        ` : ''}
    `;
}

function closeDayPanel() {
    const layout = document.querySelector('.calendar-layout');
    if (layout) {
        layout.classList.remove('day-panel-open');
        layout.classList.remove('event-detail-open');
    }
}

function closeEventDetail() {
    const layout = document.querySelector('.calendar-layout');
    if (layout) {
        layout.classList.remove('event-detail-open');
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}