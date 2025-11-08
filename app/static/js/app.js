// That gets the tags from the text box. We use split to separate the different tags by comma
// and at the same time we use indexOf to define the : symbol between key:value
function parseTags(input) {
  //Empty arrow
  const out = {};
  //Split by comma, trim spaces, and remove any empty string from the array
  input
    .split(',')
    .map(s => s.trim())
    .filter(Boolean)
    .forEach(pair => {
      //Find the index of the : (eg position 5)
      const idx = pair.indexOf(':');
      //Id not empty then get from 0 to : as k (key) and from :+1 to the end as v (value)
      if (idx > 0) {
        const k = pair.slice(0, idx).trim();
        const v = pair.slice(idx + 1).trim();
        if (k) out[k] = v;
      }
    });
  return out;
}

// Add grey tags after enter (YES chatGPT made this for me)
function renderChips(tags) {
  const holder = document.getElementById('tag-chips');
  //Clear any saved tags
  holder.innerHTML = '';
  //Goes through each key value pair in the tags dictionary
  Object.entries(tags).forEach(([k, v]) => {
    //Creates the span element with the badge class from bootstrap
    const span = document.createElement('span');
    span.className = 'badge text-bg-secondary';
    span.textContent = k + ':' + v;
    span.style.cursor = 'pointer';
    span.title = 'Click to remove';
    span.onclick = () => {
      delete tags[k];
      renderChips(tags);
      syncTags(tags);
    };
    holder.appendChild(span);
  });
}

//Sync tags to json hidden input
function syncTags(tags) {
  document.getElementById('tags-json').value = JSON.stringify(tags);
}

//Creates ampty dictionary to hold tags
const tags = {};
//Adding this so we can use the negate option in tags
const uploadedIds = new Set();

//Once the page is loaded we run the following code and add event listeners based on the input in the html form. 
document.addEventListener('DOMContentLoaded', () => {
  const tagsInput    = document.getElementById('tags-input');
  const regionSel    = document.getElementById('region');
  const uploadRegion = document.getElementById('upload-region');
  const invertBtn    = document.getElementById('invert-btn');

  // Read preselect IDs & region from URL
  //Option 1: Add the ones we want.
  const params      = new URLSearchParams(window.location.search);
  const idsParam    = params.get('ids');
  const regionParam = params.get('region');
  let preselect     = new Set();

  if (regionParam && regionSel) {
    const opt = Array.from(regionSel.options).find(o => o.value === regionParam);
    if (opt) regionSel.value = regionParam;
  }

  // Populates both preselect that will be used to check instances from list and uploadedIds
  // that will be used to negate select all other isntances that are not in the list.
  if (idsParam) {
    idsParam
      .split(',')
      .map(s => s.trim())
      .filter(Boolean)
      .forEach(id => {
        preselect.add(id);
        uploadedIds.add(id);
      });
  }

  //Negate Selection
  if (invertBtn) {
    invertBtn.addEventListener('click', () => {
      if (uploadedIds.size === 0) {
        alert('No isntances in the list');
        return;
      }
      document.querySelectorAll('.row-check').forEach(cb => {
        const id = cb.value;
        cb.checked = !uploadedIds.has(id);
      });
    });
  }

  function refreshInstances() {
    if (!regionSel) return;
    const region = regionSel.value;
    //Sends a call to Flask route /api/instances with the selected region as parameter
    fetch('/api/instances?region=' + encodeURIComponent(region))
      .then(r => r.json())
      .then(data => {
        const tbody = document.querySelector('#instances-table tbody');
        if (!tbody) return;
        tbody.innerHTML = '';
        // Error hanlding in cases no AWS profile is selected or AWS returns an error (eg permissions)
        if (data.error) {
          tbody.innerHTML =
            '<tr><td colspan="6" class="text-danger">' + data.error + '</td></tr>';
          return;
        }
        //One table row per instance
        data.instances.forEach(i => {
          const tr = document.createElement('tr');
          tr.innerHTML = `
            <td><input type="checkbox" class="row-check" name="selected_ids" value="${i.InstanceId}"></td>
            <td class="mono">${i.InstanceId}</td>
            <td>${i.Name || ''}</td>
            <td>${i.Type || ''}</td>
            <td>${i.AZ || ''}</td>
            <td>${i.State || ''}</td>
          `;
          //Adds this row to the table body
          tbody.appendChild(tr);
          // Checks for checked boxes based on preselect set created from URL parameters
          const cb = tr.querySelector('.row-check');
          if (cb && preselect.has(i.InstanceId)) cb.checked = true;
        });
        // Clear preselect after first paint to avoid reselecting on manual refresh
        preselect.clear();
      })
      .catch(err => {
        console.error('Error loading instances:', err);
      });
  }

  // Event listeners for various buttons and inputs
  const refreshBtn = document.getElementById('refresh-btn');
  if (refreshBtn) {
    document.getElementById('refresh-btn').addEventListener('click', refreshInstances);
  }

  if (regionSel) {
    regionSel.addEventListener('change', () => {
      if (uploadRegion) uploadRegion.value = regionSel.value;
      refreshInstances();
    });
  }

  const selectAll = document.getElementById('select-all');
  if (selectAll) {
    document.getElementById('select-all').addEventListener('change', (e) => {
      document.querySelectorAll('.row-check').forEach(cb => cb.checked = e.target.checked);
    });
  }

  //Search filter
  const filterInput = document.getElementById('filter');
  if (filterInput) {
    document.getElementById('filter').addEventListener('input', (e) => {
      //makes it case insensitive
      const q = e.target.value.toLowerCase();
      //Check all table rows and hide those that do not match the query
      document.querySelectorAll('#instances-table tbody tr').forEach(tr => {
        const text = tr.innerText.toLowerCase();
        //If the text is included in the row the set value to "" and show it otherwise hide it
        tr.style.display = text.includes(q) ? '' : 'none';
      });
    });
  }

  // Press enter to add tags - DOES not submit form by pressing enter (or maybe it does who knows)
  if (tagsInput) {
    tagsInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        const raw = tagsInput.value.trim();
        if (!raw) return;
        const parsed = parseTags(raw);
        Object.assign(tags, parsed);
        tagsInput.value = '';
        renderChips(tags);
        syncTags(tags);
      }
    });
  }

  //This function runs when the form is submitted (BEFORE) Before /tagger/execute is called
  //This hangles the posibility that the user does not press enter.
  const taggerForm = document.getElementById('tagger-form');
  if (taggerForm) {
    document.getElementById('tagger-form').addEventListener('submit', (e) => {
      if (tagsInput && tagsInput.value.trim()) {
        const parsed = parseTags(tagsInput.value);
        Object.assign(tags, parsed);
        tagsInput.value = '';
        renderChips(tags);
        syncTags(tags);
      }
      // We do NOT touch selected_ids here; the checkboxes already submit them.
    });
  }

  refreshInstances();
  syncTags(tags);
});
