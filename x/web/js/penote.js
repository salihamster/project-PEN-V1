// ========================================
// PENOTE - NOTES MANAGEMENT
// ========================================

import { els } from './dom.js';
import { renderMarkup, scrollToBottom as utilScrollToBottom, getFileIconClass, formatFileSize } from './utils.js';

let currentNote = null;
let notes = [];
let currentCategory = 'all';
let autoSaveTimeout = null;
let markdownModeEnabled = true;
let lastFocusedPage = null;

// ======================================== 
// PAGINATION LOGIC
// ========================================

const A4_HEIGHT = 1123; // px (at 96 DPI)
const PAGE_PADDING = 120; // Top + Bottom padding (60px + 60px)

function initPagination() {
    const container = document.getElementById('penoteEditorContent');
    if (!container) return;

    // Convert existing content to page structure if needed
    if (!container.querySelector('.penote-sheet')) {
        const content = container.innerHTML;
        container.innerHTML = '';
        createNewPage(content);
    }

    // Set initial focus page
    const firstPage = container.querySelector('.penote-sheet');
    if (firstPage) lastFocusedPage = firstPage;

    container.addEventListener('input', (e) => {
        // Debounce pagination to avoid performance kill on every keystroke
        // but fast enough to feel responsive
        requestAnimationFrame(() => paginate());
        updateWordCount();
        scheduleAutoSave();
    });

    // Live Markdown Triggers (Mode 2)
    container.addEventListener('keyup', (e) => {
        handleMarkdownTriggers(e);
    });
    
    // Handle paste to ensure pagination happens immediately
    container.addEventListener('paste', () => {
        setTimeout(paginate, 10);
    });
}

function handleMarkdownTriggers(e) {
    if (!markdownModeEnabled) return;
    if (e.key !== ' ' && e.key !== 'Enter') return;

    const selection = window.getSelection();
    if (!selection.rangeCount) return;

    const range = selection.getRangeAt(0);
    const node = range.startContainer;

    // We only care if we are inside a text node
    if (node.nodeType !== 3) return;

    const text = node.textContent;
    const parentBlock = node.parentElement;

    // Check strict equality to avoid triggering in the middle of sentences for block starters
    // Only trigger if the caret is at the end of the trigger sequence? 
    // Actually, for things like '# ', we usually check if the block STARTS with it.

    // 1. HEADERS (#, ##, ###)
    if (e.key === ' ') {
        if (parentBlock.tagName === 'P' || parentBlock.tagName === 'DIV') {
            if (text === '# ' || text === '#\u00A0') { // \u00A0 is &nbsp;
                document.execCommand('formatBlock', false, '<h1>');
                // Remove the trigger characters
                const sel = window.getSelection();
                if (sel.focusNode) sel.focusNode.textContent = '';
                e.preventDefault();
            } else if (text === '## ' || text === '##\u00A0') {
                document.execCommand('formatBlock', false, '<h2>');
                const sel = window.getSelection();
                if (sel.focusNode) sel.focusNode.textContent = '';
                e.preventDefault();
            } else if (text === '### ' || text === '###\u00A0') {
                document.execCommand('formatBlock', false, '<h3>');
                const sel = window.getSelection();
                if (sel.focusNode) sel.focusNode.textContent = '';
                e.preventDefault();
            }
            // 2. LISTS (-, *, 1.)
            else if (text === '- ' || text === '* ') {
                document.execCommand('insertUnorderedList', false, null);
                const sel = window.getSelection();
                if (sel.focusNode) sel.focusNode.textContent = '';
                e.preventDefault();
            }
            else if (text === '1. ') {
                document.execCommand('insertOrderedList', false, null);
                const sel = window.getSelection();
                if (sel.focusNode) sel.focusNode.textContent = '';
                e.preventDefault();
            }
            // 3. BLOCKQUOTE (>)
            else if (text === '> ') {
                document.execCommand('formatBlock', false, '<blockquote>');
                const sel = window.getSelection();
                if (sel.focusNode) sel.focusNode.textContent = '';
                e.preventDefault();
            }
        }
        
        // 4. INLINE FORMATTING (Bold, Italic, Strike) on Space
        // We look backwards from cursor. Simple regex check.
        // **bold** 
        const cursorOffset = range.startOffset;
        const textBefore = text.substring(0, cursorOffset);
        
        // Bold: **text**
        const boldMatch = textBefore.match(/\*\*(.+?)\*\*$/);
        if (boldMatch) {
            // This is tricky with execCommand. We might need manual range manipulation.
            // For stability in this simple version, let's stick to Block triggers mostly.
            // Inline replacement is complex to do robustly without a library.
        }
    }

    // 5. HORIZONTAL RULE (---) on Enter
    if (e.key === 'Enter') {
        // We look at the PREVIOUS sibling or the line we just left.
        // Since 'Enter' just happened, the cursor is likely in a new empty block, 
        // and the '---' is in the previous block.
        
        let previousBlock = parentBlock.previousElementSibling;
        
        // Sometimes Enter splits the text node, so we check carefully.
        // But if user typed '---' then Enter, '---' is likely its own block now.
        if (previousBlock && (previousBlock.textContent.trim() === '---')) {
            // Replace previous block with HR
            const hr = document.createElement('hr');
            previousBlock.parentNode.replaceChild(hr, previousBlock);
            e.preventDefault(); // Enter was already processed, but we modify the result
        }
        
        // Also check Strikethrough ~~text~~ on Enter
        if (previousBlock) {
             const prevText = previousBlock.innerHTML;
             const strikeMatch = prevText.match(/~~(.+?)~~/);
             if (strikeMatch) {
                 // Replace all instances
                 previousBlock.innerHTML = prevText.replace(/~~(.+?)~~/g, '<del>$1</del>');
             }
             
             // Check Bold **text** on Enter
             const boldMatch = prevText.match(/\*\*(.+?)\*\*/);
             if (boldMatch) {
                 previousBlock.innerHTML = previousBlock.innerHTML.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
             }
        }
    }
}

function createNewPage(initialContent = '<p><br></p>') {
    const container = document.getElementById('penoteEditorContent');
    const pageCount = container.querySelectorAll('.penote-sheet').length + 1;
    
    const page = document.createElement('div');
    page.className = 'penote-sheet';
    page.contentEditable = true;
    page.setAttribute('data-page-number', pageCount);
    page.innerHTML = initialContent;
    
    // Ensure paragraphs
    if (!page.innerHTML.trim()) {
        page.innerHTML = '<p><br></p>';
    }

    // Track focus
    page.addEventListener('focus', () => {
        lastFocusedPage = page;
    });

    container.appendChild(page);
    return page;
}

function paginate() {
    const container = document.getElementById('penoteEditorContent');
    const pages = Array.from(container.querySelectorAll('.penote-sheet'));
    
    let focusedElement = document.activeElement;
    let selection = window.getSelection();
    let range = selection.rangeCount > 0 ? selection.getRangeAt(0) : null;
    
    // Save cursor state details to restore later
    let cursorData = null;
    if (range && container.contains(focusedElement)) {
        cursorData = {
            node: range.startContainer,
            offset: range.startOffset,
            isText: range.startContainer.nodeType === 3
        };
    }

    let contentMoved = false;

    // Check each page for overflow
    for (let i = 0; i < pages.length; i++) {
        const page = pages[i];
        
        // While page content height > allowed height
        while (page.scrollHeight > A4_HEIGHT) {
            contentMoved = true;
            
            // Get the last node
            const lastChild = page.lastElementChild;
            if (!lastChild) break; // Should not happen
            
            // SAFEGUARD: If the page has only one element and it's still overflowing,
            // we can't move it to the next page because it will likely overflow there too,
            // causing an infinite loop. We stop pagination for this page.
            if (page.children.length === 1) {
                // console.warn('Element too large for page, stopping pagination for this block.');
                break;
            }

            // Get or create next page
            let nextPage = pages[i + 1];
            if (!nextPage) {
                nextPage = createNewPage('');
                pages.push(nextPage); // Update our local list
            }
            
            // Move last child to next page (at the top)
            if (nextPage.firstChild) {
                nextPage.insertBefore(lastChild, nextPage.firstChild);
            } else {
                nextPage.appendChild(lastChild);
            }
            
            // Refocus if we moved the active node
            if (cursorData && (lastChild === cursorData.node || lastChild.contains(cursorData.node))) {
                // We moved the cursor's node!
                // We will rely on browser default behavior mostly, but might need to re-set selection
                
                // Re-setting range
                try {
                    const newRange = document.createRange();
                    newRange.setStart(cursorData.node, cursorData.offset);
                    newRange.collapse(true);
                    selection.removeAllRanges();
                    selection.addRange(newRange);
                    nextPage.focus(); // Ensure the page itself is focused
                } catch(e) {
                    // Fallback if node became invalid
                    console.warn("Cursor restore failed", e);
                }
            }
        }
    }
}

// ========================================
// INITIALIZATION
// ========================================

export function setupPENote() {
    const notesBtn = document.getElementById('notesBtn');
    const penoteBackBtn = document.getElementById('penoteBackBtn');
    const penoteNewNoteBtn = document.getElementById('penoteNewNoteBtn');
    const penoteSaveBtn = document.getElementById('penoteSaveBtn');
    const penoteDeleteBtn = document.getElementById('penoteDeleteBtn');
    const penoteNotesToggle = document.getElementById('penoteNotesToggle');
    const penoteSidebarCloseBtn = document.getElementById('penoteSidebarCloseBtn');
    const penoteEmptyCreateBtn = document.getElementById('penoteEmptyCreateBtn');
    const penoteCenterCreateBtn = document.getElementById('penoteCenterCreateBtn');
    const penoteTitleInput = document.getElementById('penoteTitleInput');
    const penoteEditorContent = document.getElementById('penoteEditorContent');
    const penoteSearchInput = document.getElementById('penoteSearchInput');

    // Open PENote
    if (notesBtn) {
        notesBtn.addEventListener('click', openPENote);
    }

    // Close PENote
    if (penoteBackBtn) {
        penoteBackBtn.addEventListener('click', closePENote);
    }

    // New Note
    if (penoteNewNoteBtn) {
        penoteNewNoteBtn.addEventListener('click', createNewNote);
    }

    if (penoteEmptyCreateBtn) {
        penoteEmptyCreateBtn.addEventListener('click', createNewNote);
    }

    if (penoteCenterCreateBtn) {
        penoteCenterCreateBtn.addEventListener('click', createNewNote);
    }

    // Save Note
    if (penoteSaveBtn) {
        penoteSaveBtn.addEventListener('click', saveCurrentNote);
    }

    // Delete Note
    if (penoteDeleteBtn) {
        penoteDeleteBtn.addEventListener('click', deleteCurrentNote);
    }

    // Notes Sidebar Toggle
    if (penoteNotesToggle) {
        penoteNotesToggle.addEventListener('click', toggleNotesSidebar);
    }
    
    if (penoteSidebarCloseBtn) {
        penoteSidebarCloseBtn.addEventListener('click', toggleNotesSidebar);
    }

    // Title Input
    if (penoteTitleInput) {
        penoteTitleInput.addEventListener('input', () => {
            if (currentNote) {
                currentNote.title = penoteTitleInput.value || 'Başlıksız Not';
                scheduleAutoSave();
            }
        });
    }

    // Editor Content - handled by initPagination() now
    // But we still need keydown for shortcuts to work via bubbling
    if (penoteEditorContent) {
        // Keyboard shortcuts (Delegation)
        penoteEditorContent.addEventListener('keydown', handleEditorKeydown);
    }

    // Search
    if (penoteSearchInput) {
        penoteSearchInput.addEventListener('input', (e) => {
            filterNotes(e.target.value);
        });
    }

    // Category Tabs
    document.querySelectorAll('.penote-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.penote-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            currentCategory = tab.dataset.category;
            loadNotes();
        });
    });

    // Toolbar Buttons
    document.querySelectorAll('.penote-toolbar-btn').forEach(btn => {
        if (btn.id === 'toggleMarkdownBtn') return; // Skip toggle button, handled separately
        
        // Use mousedown to prevent focus loss from editor
        btn.addEventListener('mousedown', (e) => {
            e.preventDefault(); // This is crucial
            const action = btn.dataset.action;
            executeToolbarAction(action);
        });
    });

    // Markdown Toggle
    const toggleMarkdownBtn = document.getElementById('toggleMarkdownBtn');
    if (toggleMarkdownBtn) {
        toggleMarkdownBtn.addEventListener('click', () => {
            markdownModeEnabled = !markdownModeEnabled;
            toggleMarkdownBtn.classList.toggle('active', markdownModeEnabled);
            showStatus(markdownModeEnabled ? 'Otomatik Format: Açık' : 'Otomatik Format: Kapalı', 'success');
        });
    }

    // Initialize Pagination System
    initPagination();

    console.log('PENote initialized');
}

// ========================================
// PAGE NAVIGATION
// ========================================

function openPENote() {
    const penotePage = document.getElementById('penotePage');
    const appContainer = document.querySelector('.app');
    
    if (penotePage) {
        penotePage.classList.add('open');
        if (appContainer) {
            appContainer.classList.add('penote-open');
        }
        
        if (!currentNote) {
            showEditor(false);
        } else {
            showEditor(true);
        }

        loadNotes();
    }
}

function closePENote() {
    const penotePage = document.getElementById('penotePage');
    const appContainer = document.querySelector('.app');
    
    if (penotePage) {
        penotePage.classList.remove('open');
        if (appContainer) {
            appContainer.classList.remove('penote-open');
        }
        if (currentNote && currentNote.modified) {
            saveCurrentNote();
        }
    }
}

// ======================================== 
// NOTES MANAGEMENT
// ========================================

async function loadNotes() {
    try {
        const response = await fetch('/api/pen/notes/list?category=' + currentCategory);
        const data = await response.json();
        
        if (data.status === 'success') {
            notes = data.notes || [];
            renderNotesList();
        }
    } catch (error) {
        console.error('Failed to load notes:', error);
        showStatus('Notlar yüklenemedi', 'error');
    }
}

function renderNotesList() {
    const penoteList = document.getElementById('penoteList');
    if (!penoteList) return;

    if (notes.length === 0) {
        penoteList.innerHTML = `
            <div class="penote-empty">
                <i class="fas fa-sticky-note"></i>
                <span>Henüz not yok</span>
                <button class="penote-empty-btn" id="penoteEmptyCreateBtn">
                    <i class="fas fa-plus"></i> Yeni Not Oluştur
                </button>
            </div>
        `;
        
        // Re-attach event listener
        const btn = document.getElementById('penoteEmptyCreateBtn');
        if (btn) {
            btn.addEventListener('click', createNewNote);
        }
        return;
    }

    const html = notes.map(note => `
        <div class="penote-item ${currentNote && currentNote.path === note.path ? 'active' : ''}" 
             data-path="${note.path}">
            <div class="penote-item-header">
                <span class="penote-item-title">${escapeHtml(note.title)}</span>
                <i class="penote-item-icon fas fa-sticky-note"></i>
            </div>
            <div class="penote-item-preview">${escapeHtml(note.preview)}</div>
            <div class="penote-item-meta">
                <span class="penote-item-date">
                    <i class="fas fa-clock"></i>
                    ${formatDate(note.modified)}
                </span>
                <span class="penote-item-category">${getCategoryLabel(note.category)}</span>
            </div>
        </div>
    `).join('');

    penoteList.innerHTML = html;

    // Attach click events
    document.querySelectorAll('.penote-item').forEach(item => {
        item.addEventListener('click', () => {
            const path = item.dataset.path;
            const note = notes.find(n => n.path === path);
            if (note) {
                loadNote(note);
            }
        });
    });
}

function showEditor(visible) {
    const panel = document.getElementById('penoteEditorPanel');
    if (visible) {
        panel.classList.remove('no-note-selected');
    } else {
        panel.classList.add('no-note-selected');
    }
}

async function loadNote(note) {
    try {
        const response = await fetch(`/api/pen/file-content?name=${encodeURIComponent(note.path)}`);
        const data = await response.json();
        
        if (data.exists) {
            currentNote = {
                path: note.path,
                title: note.title,
                content: data.content,
                category: note.category,
                modified: false
            };

            // Update UI
            showEditor(true);
            document.getElementById('penoteTitleInput').value = note.title;
            
            // Render content into pages
            const container = document.getElementById('penoteEditorContent');
            container.innerHTML = ''; // Clear existing
            
            const firstPage = createNewPage(htmlToEditor(data.content));
            
            // Run pagination to split content if needed
            setTimeout(() => {
                paginate();
                updateWordCount();
            }, 50);

            showStatus('Not yüklendi', 'success');
            
            // Update active state
            document.querySelectorAll('.penote-item').forEach(item => {
                item.classList.toggle('active', item.dataset.path === note.path);
            });
        }
    } catch (error) {
        console.error('Failed to load note:', error);
        showStatus('Not yüklenemedi', 'error');
    }
}

function createNewNote() {
    showEditor(true);
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    const category = currentCategory === 'all' ? 'notes' : currentCategory;
    const path = `${category}/yeni-not-${timestamp}.md`;

    currentNote = {
        path: path,
        title: 'Başlıksız Not',
        content: '',
        category: category,
        modified: true,
        isNew: true
    };

    document.getElementById('penoteTitleInput').value = 'Başlıksız Not';
    
    // Reset pages
    const container = document.getElementById('penoteEditorContent');
    container.innerHTML = '';
    const page = createNewPage('<p><br></p>');
    page.focus();

    updateWordCount();
    showStatus('Yeni not oluşturuldu', 'success');
}

async function saveCurrentNote() {
    if (!currentNote) return;

    try {
        showStatus('Kaydediliyor...', 'saving');

        // Aggregate content from all pages
        const pages = document.querySelectorAll('.penote-sheet');
        let fullHtml = '';
        pages.forEach(page => {
            fullHtml += page.innerHTML;
        });

        const markdownContent = editorToMarkdown(fullHtml);

        const response = await fetch('/api/pen/workspace/write', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                path: currentNote.path,
                content: markdownContent
            })
        });

        const data = await response.json();

        if (data.status === 'success') {
            currentNote.modified = false;
            currentNote.isNew = false;
            showStatus('Kaydedildi', 'success');
            await loadNotes();
        } else {
            showStatus('Kaydetme başarısız', 'error');
        }
    } catch (error) {
        console.error('Failed to save note:', error);
        showStatus('Kaydetme hatası', 'error');
    }
}

async function deleteCurrentNote() {
    if (!currentNote || currentNote.isNew) return;

    if (!confirm(`"${currentNote.title}" notunu silmek istediğinizden emin misiniz?`)) {
        return;
    }

    try {
        // TODO: Implement delete API endpoint
        showStatus('Not silindi', 'success');
        currentNote = null;
        document.getElementById('penoteTitleInput').value = '';
        
        const container = document.getElementById('penoteEditorContent');
        container.innerHTML = '';
        createNewPage();
        
        await loadNotes();
    } catch (error) {
        console.error('Failed to delete note:', error);
        showStatus('Silme hatası', 'error');
    }
}

function scheduleAutoSave() {
    if (!currentNote) return;
    
    currentNote.modified = true;
    
    if (autoSaveTimeout) {
        clearTimeout(autoSaveTimeout);
    }

    autoSaveTimeout = setTimeout(() => {
        saveCurrentNote();
    }, 2000); // Auto-save after 2 seconds of inactivity
}

// ======================================== 
// EDITOR TOOLBAR ACTIONS
// ========================================

function executeToolbarAction(action) {
    let editor = document.activeElement;
    
    // If focus is lost (e.g. clicked button), try to restore to last known page
    if (!editor || !editor.classList.contains('penote-sheet')) {
        if (lastFocusedPage && document.contains(lastFocusedPage)) {
            editor = lastFocusedPage;
            editor.focus();
        } else {
            // Try to find the first page
            const firstPage = document.querySelector('.penote-sheet');
            if (firstPage) {
                editor = firstPage;
                editor.focus();
                lastFocusedPage = firstPage;
            } else {
                return;
            }
        }
    }

    switch (action) {
        case 'bold':
            document.execCommand('bold', false, null);
            break;
        case 'italic':
            document.execCommand('italic', false, null);
            break;
        case 'underline':
            document.execCommand('underline', false, null);
            break;
        case 'strikethrough':
            document.execCommand('strikeThrough', false, null);
            break;
        case 'hr':
            document.execCommand('insertHorizontalRule', false, null);
            break;
        case 'h1':
            document.execCommand('formatBlock', false, '<h1>');
            break;
        case 'h2':
            document.execCommand('formatBlock', false, '<h2>');
            break;
        case 'h3':
            document.execCommand('formatBlock', false, '<h3>');
            break;
        case 'ul':
            document.execCommand('insertUnorderedList', false, null);
            break;
        case 'ol':
            document.execCommand('insertOrderedList', false, null);
            break;
        case 'quote':
            document.execCommand('formatBlock', false, '<blockquote>');
            break;
        case 'code':
            const selection = window.getSelection();
            if (selection.rangeCount > 0) {
                const range = selection.getRangeAt(0);
                const code = document.createElement('code');
                code.textContent = range.toString();
                range.deleteContents();
                range.insertNode(code);
            }
            break;
        case 'link':
            const url = prompt('Bağlantı URL\'si:');
            if (url) {
                document.execCommand('createLink', false, url);
            }
            break;
        case 'image':
            const imgUrl = prompt('Resim URL\'si:');
            if (imgUrl) {
                document.execCommand('insertImage', false, imgUrl);
            }
            break;
        case 'undo':
            document.execCommand('undo', false, null);
            break;
        case 'redo':
            document.execCommand('redo', false, null);
            break;
    }
}

function handleEditorKeydown(e) {
    // Ctrl+B - Bold
    if (e.ctrlKey && e.key === 'b') {
        e.preventDefault();
        executeToolbarAction('bold');
    }
    // Ctrl+I - Italic
    else if (e.ctrlKey && e.key === 'i') {
        e.preventDefault();
        executeToolbarAction('italic');
    }
    // Ctrl+U - Underline
    else if (e.ctrlKey && e.key === 'u') {
        e.preventDefault();
        executeToolbarAction('underline');
    }
    // Ctrl+S - Save
    else if (e.ctrlKey && e.key === 's') {
        e.preventDefault();
        saveCurrentNote();
    }
}

// ======================================== 
// PANEL TOGGLES
// ========================================
function toggleNotesSidebar() {
    const layout = document.querySelector('.penote-layout');
    if (layout) {
        layout.classList.toggle('notes-open');
    }
}

// ======================================== 
// UTILITY FUNCTIONS
// ========================================

function updateWordCount() {
    const pages = document.querySelectorAll('.penote-page');
    let text = '';
    pages.forEach(p => text += (p.innerText || '') + ' ');
    
    const words = text.trim().split(/\s+/).filter(w => w.length > 0).length;
    
    const infoEl = document.getElementById('penoteInfo');
    if (infoEl) {
        infoEl.textContent = `${words} kelime`;
    }
}

function showStatus(message, type = 'success') {
    const statusEl = document.getElementById('penoteStatus');
    if (statusEl) {
        statusEl.textContent = message;
        statusEl.className = `penote-status ${type}`;
    }
}

function filterNotes(query) {
    const lowerQuery = query.toLowerCase();
    const filtered = notes.filter(note => 
        note.title.toLowerCase().includes(lowerQuery) ||
        note.preview.toLowerCase().includes(lowerQuery)
    );
    
    // Re-render with filtered notes
    const tempNotes = notes;
    notes = filtered;
    renderNotesList();
    notes = tempNotes;
}

function getCategoryLabel(category) {
    const labels = {
        'notes': 'Not',
        'daily_plans': 'Günlük',
        'projects': 'Proje',
        'uploads': 'Yükleme'
    };
    return labels[category] || category;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) return 'Bugün';
    if (days === 1) return 'Dün';
    if (days < 7) return `${days} gün önce`;
    
    return date.toLocaleDateString('tr-TR', { 
        day: 'numeric', 
        month: 'short',
        year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ======================================== 
// MARKDOWN CONVERSION
// ========================================

function editorToMarkdown(html) {
    // Simple HTML to Markdown conversion
    let md = html;
    
    // Horizontal Rule
    md = md.replace(/<hr\s*\/?>/gi, '---\n\n');

    // Headers
    md = md.replace(/<h1>(.*?)<\/h1>/gi, '# $1\n\n');
    md = md.replace(/<h2>(.*?)<\/h2>/gi, '## $1\n\n');
    md = md.replace(/<h3>(.*?)<\/h3>/gi, '### $1\n\n');
    
    // Bold, Italic, Strikethrough
    md = md.replace(/<strong>(.*?)<\/strong>/gi, '**$1**');
    md = md.replace(/<b>(.*?)<\/b>/gi, '**$1**');
    md = md.replace(/<em>(.*?)<\/em>/gi, '*$1*');
    md = md.replace(/<i>(.*?)<\/i>/gi, '*$1*');
    md = md.replace(/<del>(.*?)<\/del>/gi, '~~$1~~');
    md = md.replace(/<s>(.*?)<\/s>/gi, '~~$1~~');
    md = md.replace(/<strike>(.*?)<\/strike>/gi, '~~$1~~');
    
    // Links
    md = md.replace(/<a href="(.*?)">(.*?)<\/a>/gi, '[$2]($1)');
    
    // Images
    md = md.replace(/<img src="(.*?)" alt="(.*?)">/gi, '![$2]($1)');
    md = md.replace(/<img src="(.*?)">/gi, '![]($1)');
    
    // Lists
    md = md.replace(/<ul>(.*?)<\/ul>/gis, (match, content) => {
        return content.replace(/<li>(.*?)<\/li>/gi, '- $1\n');
    });
    md = md.replace(/<ol>(.*?)<\/ol>/gis, (match, content) => {
        let counter = 1;
        return content.replace(/<li>(.*?)<\/li>/gi, () => `${counter++}. $1\n`);
    });
    
    // Blockquote
    md = md.replace(/<blockquote>(.*?)<\/blockquote>/gis, '> $1\n\n');
    
    // Code
    md = md.replace(/<code>(.*?)<\/code>/gi, '`$1`');
    md = md.replace(/<pre><code>(.*?)<\/code><\/pre>/gis, '```\n$1\n```\n\n');
    
    // Paragraphs and Divs (for contentEditable compatibility)
    md = md.replace(/<p>(.*?)<\/p>/gi, '$1\n\n');
    md = md.replace(/<div>(.*?)<\/div>/gi, '$1\n'); // Divs usually mean single line break
    md = md.replace(/<br\s*\/?>/gi, '\n');
    
    // Remove remaining HTML tags
    md = md.replace(/<[^>]+>/g, '');
    
    // Clean up
    // md = md.replace(/\n{3,}/g, '\n\n'); // Allow multiple empty lines
    md = md.trim();
    
    return md;
}

function htmlToEditor(markdown) {
    // Simple Markdown to HTML conversion for editor
    let html = markdown;
    
    // Headers
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');
    
    // Horizontal Rule
    html = html.replace(/^---$/gim, '<hr>');

    // Bold, Italic, Strikethrough
    // Bold: Match **text**, allow single * inside.
    html = html.replace(/\*\*((?:[^*]|\*[^*])*?)\*\*/g, '<strong>$1</strong>');
    
    // Italic: Match *text*, ensure not part of ** (lookaround).
    html = html.replace(/(?<!\*)\*((?:[^*]|\*[^*])+?)\*(?!\*)/g, '<em>$1</em>');
    
    html = html.replace(/~~(.*?)~~/g, '<del>$1</del>');
    
    // Links
    html = html.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2">$1</a>');
    
    // Images
    html = html.replace(/!\[(.*?)\]\((.*?)\)/g, '<img src="$2" alt="$1">');
    
    // Code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Lists
    html = html.replace(/^\- (.*$)/gim, '<li>$1</li>');
    // Regex for grouping consecutive li elements into ul
    // Use positive lookahead for newline or end of string to stop the group
    html = html.replace(/((?:<li>.*?<\/li>(?:\r?\n)*)+)/g, '<ul>$1</ul>\n\n');
    
    // Paragraphs
    html = html.split('\n\n').map(para => {
        if (!para.trim()) return '<p><br></p>'; // Handle empty lines
        if (!para.match(/^<[h|u|o|l|b|p|d|s]/)) { // Added check for other block tags
            return `<p>${para}</p>`;
        }
        return para;
    }).join('');
    
    return html;
}
