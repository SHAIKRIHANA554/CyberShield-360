/**
 * Admin education management and user activity dashboard.
 */
(function () {
  if (!requireAdmin()) return;

  document.getElementById('navbar-container').innerHTML = renderNavbar(true);
  initPage();

  const contentCache = { news: [], learning: [], law: [], quiz: [] };
  const contentConfig = {
    news: { endpoint: ENDPOINTS.ADMIN_NEWS, listId: 'newsItems', formId: 'newsForm', heading: 'news' },
    learning: { endpoint: ENDPOINTS.ADMIN_LEARNING, listId: 'learningItems', formId: 'learningForm', heading: 'learning' },
    law: { endpoint: ENDPOINTS.ADMIN_LEARNING, listId: 'lawItems', formId: 'lawForm', heading: 'law' },
    quiz: { endpoint: ENDPOINTS.ADMIN_QUIZ, listId: 'quizItems', formId: 'quizForm', heading: 'quiz' }
  };

  function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, character => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    })[character]);
  }

  function getListEndpoint(type) {
    if (type === 'learning') return `${ENDPOINTS.ADMIN_LEARNING}?type=article`;
    if (type === 'law') return `${ENDPOINTS.ADMIN_LEARNING}?type=cyber_law`;
    return contentConfig[type].endpoint;
  }

  async function loadStats() {
    const result = await apiGet(ENDPOINTS.ADMIN_DASHBOARD);
    if (!result.success) return;
    const stats = result.data;
    document.getElementById('usersCount').textContent = stats.users_count || 0;
    document.getElementById('loginCount').textContent = stats.logged_in_users_24h || 0;
    document.getElementById('learningCompletion').textContent = `${stats.learning_progress?.completion_percentage || 0}%`;
    document.getElementById('quizAttempts').textContent = stats.quiz_attempts_count || 0;
  }

  async function loadUsers() {
    const result = await apiGet(`${ENDPOINTS.ADMIN_USERS}?per_page=100`);
    const table = document.getElementById('usersTable');
    if (!result.success) {
      table.innerHTML = `<tr><td colspan="5" class="text-secondary">${escapeHtml(result.message || 'User activity is unavailable.')}</td></tr>`;
      return;
    }

    const users = result.data.items || [];
    table.innerHTML = users.length ? users.map(user => `
      <tr>
        <td><div class="fw-semibold">${escapeHtml(user.name)}</div><div class="small text-secondary">${escapeHtml(user.email)}</div></td>
        <td>${user.learning_completed || 0} / ${user.learning_total || 0}<div class="small text-secondary">${user.learning_average_progress || 0}% average</div></td>
        <td>${user.quiz_attempts || 0}</td>
        <td>${user.quiz_average_score === null ? 'No attempts' : `${user.quiz_average_score}%`}</td>
        <td>${user.last_login ? escapeHtml(formatDate(user.last_login)) : 'Never'}</td>
      </tr>
    `).join('') : '<tr><td colspan="5" class="text-secondary">No registered users yet.</td></tr>';
  }

  function contentDescription(type, item) {
    if (type === 'quiz') return `${item.questions?.length || 0} questions · ${Math.ceil((item.duration || 0) / 60)} min`;
    if (type === 'news') return item.summary || item.content || '';
    return item.description || item.content || '';
  }

  function renderContentCard(type, item) {
    const description = contentDescription(type, item);
    return `
      <div class="col-md-6">
        <article class="glass-card p-3 h-100 d-flex flex-column">
          <div class="d-flex justify-content-between align-items-start gap-2">
            <h3 class="h6 mb-2">${escapeHtml(item.title)}</h3>
            <span class="badge ${item.is_active === false ? 'bg-secondary' : 'bg-success'}">${item.is_active === false ? 'Draft' : 'Published'}</span>
          </div>
          <p class="small text-secondary flex-grow-1">${escapeHtml(description).slice(0, 220)}</p>
          <div class="d-flex gap-2">
            <button type="button" class="btn-outline-cyber btn-sm" data-content-action="edit" data-type="${type}" data-id="${escapeHtml(item._id)}" aria-label="Edit ${escapeHtml(item.title)}"><i class="fas fa-pen me-1"></i>Edit</button>
            <button type="button" class="btn-outline-cyber btn-sm text-danger" data-content-action="delete" data-type="${type}" data-id="${escapeHtml(item._id)}" aria-label="Delete ${escapeHtml(item.title)}"><i class="fas fa-trash me-1"></i>Delete</button>
          </div>
        </article>
      </div>
    `;
  }

  async function loadContent(type) {
    const target = document.getElementById(contentConfig[type].listId);
    target.innerHTML = '<div class="col-12 text-secondary">Loading...</div>';
    const result = await apiGet(getListEndpoint(type));
    if (!result.success) {
      contentCache[type] = [];
      target.innerHTML = `<div class="col-12 text-secondary">${escapeHtml(result.message || 'Content could not be loaded.')}</div>`;
      return;
    }
    contentCache[type] = result.data.items || [];
    target.innerHTML = contentCache[type].length
      ? contentCache[type].map(item => renderContentCard(type, item)).join('')
      : '<div class="col-12 text-secondary">No content has been added yet.</div>';
  }

  function addQuestionEditor(question = {}) {
    const wrapper = document.createElement('fieldset');
    wrapper.className = 'quiz-question glass-card p-3';
    const options = (question.options || []).slice(0, 4);
    while (options.length < 4) options.push('');
    wrapper.innerHTML = `
      <div class="d-flex justify-content-between align-items-center gap-2 mb-2">
        <legend class="h6 mb-0">Question</legend>
        <button type="button" class="btn-outline-cyber btn-sm remove-question" aria-label="Remove question"><i class="fas fa-xmark"></i></button>
      </div>
      <label class="form-label">Question text</label>
      <input class="form-control quiz-question-text mb-3" required maxlength="500" value="${escapeHtml(question.question || '')}">
      <div class="row g-2">
        ${options.map((option, index) => `<div class="col-sm-6"><label class="form-label small">Option ${index + 1}</label><input class="form-control quiz-option" required maxlength="300" value="${escapeHtml(option)}"></div>`).join('')}
      </div>
      <label class="form-label mt-3">Correct answer</label>
      <select class="form-select quiz-correct-answer">
        ${options.map((_, index) => `<option value="${index}" ${Number(question.correct) === index ? 'selected' : ''}>Option ${index + 1}</option>`).join('')}
      </select>
    `;
    wrapper.querySelector('.remove-question').addEventListener('click', () => {
      if (document.querySelectorAll('.quiz-question').length > 1) wrapper.remove();
    });
    document.getElementById('quizQuestionList').appendChild(wrapper);
  }

  function resetForm(type) {
    const config = contentConfig[type];
    const form = document.getElementById(config.formId);
    form.reset();
    delete form.dataset.editId;
    document.getElementById(`${type}FormHeading`).textContent = type === 'learning' ? 'Add learning module' : type === 'law' ? 'Add cyber law' : `Add ${type}`;
    document.getElementById(`${type}Submit`).textContent = type === 'learning' ? 'Add module' : type === 'law' ? 'Add law' : type === 'news' ? 'Publish news' : 'Add quiz';
    form.querySelector('[data-cancel-edit]')?.classList.add('d-none');
    if (type === 'quiz') {
      document.getElementById('quizQuestionList').innerHTML = '';
      addQuestionEditor();
    }
  }

  function editContent(type, id) {
    const item = contentCache[type].find(entry => entry._id === id);
    if (!item) return;
    const form = document.getElementById(contentConfig[type].formId);
    form.dataset.editId = id;
    document.getElementById(`${type}FormHeading`).textContent = `Edit ${type === 'learning' ? 'learning module' : type === 'law' ? 'cyber law' : type}`;
    document.getElementById(`${type}Submit`).textContent = 'Save changes';
    form.querySelector('[data-cancel-edit]')?.classList.remove('d-none');

    if (type === 'news') {
      document.getElementById('newsTitle').value = item.title || '';
      document.getElementById('newsCategory').value = item.category || '';
      document.getElementById('newsAuthor').value = item.author || '';
      document.getElementById('newsSummary').value = item.summary || '';
      document.getElementById('newsContent').value = item.content || '';
      document.getElementById('newsActive').checked = item.is_active !== false;
    } else if (type === 'learning' || type === 'law') {
      document.getElementById(`${type}Title`).value = item.title || '';
      document.getElementById(`${type}Category`).value = item.category || '';
      document.getElementById(`${type}Description`).value = item.description || '';
      document.getElementById(`${type}Content`).value = item.content || '';
      document.getElementById(`${type}Active`).checked = item.is_active !== false;
      if (type === 'learning') document.getElementById('learningDuration').value = item.duration || '';
    } else {
      document.getElementById('quizTitle').value = item.title || '';
      document.getElementById('quizDescription').value = item.description || '';
      document.getElementById('quizDuration').value = Math.max(1, Math.ceil((item.duration || 300) / 60));
      document.getElementById('quizActive').checked = item.is_active !== false;
      document.getElementById('quizQuestionList').innerHTML = '';
      (item.questions || []).forEach(question => addQuestionEditor(question));
      if (!item.questions?.length) addQuestionEditor();
    }

    form.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  async function deleteContent(type, id) {
    const item = contentCache[type].find(entry => entry._id === id);
    const confirmation = await Swal.fire({
      icon: 'warning', title: 'Delete this content?', text: item?.title || 'This cannot be undone.',
      showCancelButton: true, confirmButtonText: 'Delete', cancelButtonText: 'Keep it',
      background: '#141A26', color: '#fff'
    });
    if (!confirmation.isConfirmed) return;
    showLoading();
    const result = await apiDelete(`${contentConfig[type].endpoint}/${encodeURIComponent(id)}`);
    hideLoading();
    if (!result.success) {
      Swal.fire({ icon: 'error', title: 'Delete failed', text: result.message, background: '#141A26', color: '#fff' });
      return;
    }
    await loadContent(type);
    loadStats();
  }

  function buildPayload(type) {
    if (type === 'news') {
      const category = document.getElementById('newsCategory').value.trim();
      return {
        title: document.getElementById('newsTitle').value.trim(),
        category,
        author: document.getElementById('newsAuthor').value.trim() || 'CyberShield Admin',
        summary: document.getElementById('newsSummary').value.trim(),
        content: document.getElementById('newsContent').value.trim(),
        tags: category ? [category.toLowerCase()] : [],
        is_active: document.getElementById('newsActive').checked
      };
    }
    if (type === 'learning' || type === 'law') {
      return {
        title: document.getElementById(`${type}Title`).value.trim(),
        category: document.getElementById(`${type}Category`).value.trim(),
        description: document.getElementById(`${type}Description`).value.trim(),
        content: document.getElementById(`${type}Content`).value.trim(),
        ...(type === 'learning' ? { duration: document.getElementById('learningDuration').value.trim() || '15 min' } : {}),
        type: type === 'law' ? 'cyber_law' : 'article',
        is_active: document.getElementById(`${type}Active`).checked
      };
    }

    const questions = [...document.querySelectorAll('.quiz-question')].map(editor => ({
      question: editor.querySelector('.quiz-question-text').value.trim(),
      options: [...editor.querySelectorAll('.quiz-option')].map(option => option.value.trim()),
      correct: Number(editor.querySelector('.quiz-correct-answer').value)
    }));
    return {
      title: document.getElementById('quizTitle').value.trim(),
      description: document.getElementById('quizDescription').value.trim(),
      duration: Number(document.getElementById('quizDuration').value) * 60,
      questions,
      is_active: document.getElementById('quizActive').checked
    };
  }

  async function saveContent(type, event) {
    event.preventDefault();
    const form = event.currentTarget;
    const payload = buildPayload(type);
    if (type === 'quiz' && (!payload.questions.length || payload.questions.some(question => !question.question || question.options.some(option => !option)))) {
      Swal.fire({ icon: 'warning', title: 'Complete each question', text: 'Every question needs text and four options.', background: '#141A26', color: '#fff' });
      return;
    }

    const itemId = form.dataset.editId;
    const endpoint = contentConfig[type].endpoint;
    showLoading();
    const result = itemId
      ? await apiPut(`${endpoint}/${encodeURIComponent(itemId)}`, payload)
      : await apiPost(endpoint, payload);
    hideLoading();
    if (!result.success) {
      Swal.fire({ icon: 'error', title: 'Save failed', text: result.message, background: '#141A26', color: '#fff' });
      return;
    }

    resetForm(type);
    await loadContent(type);
    loadStats();
    Swal.fire({ icon: 'success', title: 'Saved', text: result.message || 'Content saved successfully.', timer: 1500, showConfirmButton: false, background: '#141A26', color: '#fff' });
  }

  document.addEventListener('click', event => {
    const action = event.target.closest('[data-content-action]');
    if (action) {
      const type = action.dataset.type;
      if (action.dataset.contentAction === 'edit') editContent(type, action.dataset.id);
      if (action.dataset.contentAction === 'delete') deleteContent(type, action.dataset.id);
    }
    const cancel = event.target.closest('[data-cancel-edit]');
    if (cancel) resetForm(cancel.dataset.cancelEdit);
  });

  Object.keys(contentConfig).forEach(type => {
    document.getElementById(contentConfig[type].formId).addEventListener('submit', event => saveContent(type, event));
  });
  document.getElementById('addQuizQuestion').addEventListener('click', () => addQuestionEditor());
  document.getElementById('refreshUsers').addEventListener('click', () => {
    loadUsers();
    loadStats();
  });

  showLoading();
  Promise.all([loadStats(), loadUsers(), ...Object.keys(contentConfig).map(loadContent)])
    .finally(hideLoading);
})();