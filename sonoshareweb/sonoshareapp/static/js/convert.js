/* global FormData, sessionStorage, EventSource */

document.addEventListener('DOMContentLoaded', function () {
  const playlistForm = document.getElementById('playlist-form');
  const progressContainer = document.getElementById('progress-container');
  const progressBar = document.getElementById('progress-bar');
  const progressMessage = document.getElementById('progress-bar-message');
  let eventSource = null;
  let retryCount = 0;
  const MAX_RETRIES = 3;

  function getCookie (name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  function setupEventSource (progressUrl) {
    eventSource = new EventSource(progressUrl);

    eventSource.onmessage = function (e) {
      const result = JSON.parse(e.data);
      console.log('Progress update:', result);

      if (result.complete) {
        eventSource.close();
        if (result.result && result.result.track_ids) {
          progressBar.style.width = '100%';
          progressBar.style.backgroundColor = '#4CAF50';
          progressMessage.innerHTML = 'Conversion completed!';
          sessionStorage.setItem('conversionData', JSON.stringify(result.result));
          window.location.href = '/review_playlist/';
        } else {
          progressBar.style.backgroundColor = '#ff6b6b';
          progressMessage.innerHTML = result.error || 'No tracks were converted successfully';
        }
      } else if (result.progress) {
        const percent = (result.progress.current / result.progress.total) * 100;
        progressBar.style.width = `${percent}%`;
        progressMessage.innerHTML = result.progress.description ||
          `Processing: ${result.progress.current}/${result.progress.total}`;
        retryCount = 0; // Reset retry count on successful progress
      }
    };

    eventSource.onerror = function (error) {
      console.error('EventSource error:', error);
      if (retryCount < MAX_RETRIES) {
        retryCount++;
        progressMessage.innerHTML = `Connection lost. Retry attempt ${retryCount}/${MAX_RETRIES}...`;
        setTimeout(() => setupEventSource(progressUrl), 3000);
      } else {
        eventSource.close();
        progressMessage.innerHTML = 'Connection failed after multiple attempts. Please try again.';
        progressBar.style.backgroundColor = '#ff6b6b';
      }
    };
  }

  if (playlistForm) {
    playlistForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      if (eventSource) {
        eventSource.close();
      }
      retryCount = 0;
      progressContainer.style.display = 'block';
      progressBar.style.width = '0%';
      progressMessage.innerHTML = 'Starting conversion...';

      const formData = new FormData(playlistForm);
      const csrftoken = getCookie('csrftoken');

      try {
        const response = await fetch(playlistForm.action, {
          method: 'POST',
          body: formData,
          headers: {
            'X-CSRFToken': csrftoken
          },
          credentials: 'same-origin'
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('Initial response:', data);

        if (data.task_id) {
          setupEventSource(`/celery-progress/${data.task_id}/`);
        }
      } catch (error) {
        console.error('Conversion error:', error);
        progressMessage.innerHTML = 'Failed to start conversion. Please try again.';
        progressBar.style.backgroundColor = '#ff6b6b';
      }
    });
  }
});
