// GESTIONE AJAX E FILTRI PERSISTENTI:

document.addEventListener("DOMContentLoaded", function () {
    // Funzione per salvare i filtri attuali in sessionStorage
    function saveCurrentFilters() {
        // Ottieni i valori dei filtri attuali
        const filters = {
            anno_esame: document.querySelector('select[name="anno_esame"]')?.value || '',
            periodo_esame: document.querySelector('select[name="periodo_esame"]')?.value || '',
            facolta_appelli: document.querySelector('select[name="facolta_appelli"]')?.value || '',
            aula_visible: document.querySelector('select[name="aula_visible"]')?.value || ''
        };
        
        console.log("Filtri salvati:", filters);
        
        // Salva in sessionStorage
        sessionStorage.setItem('examoreFilters', JSON.stringify(filters));
        return filters;
    }
    
    // Funzione per ripristinare i filtri salvati
    function restoreFilters() {
        // Controlla se ci sono filtri salvati
        const savedFilters = sessionStorage.getItem('examoreFilters');
        if (!savedFilters) return;
        
        // Ripristina i valori
        const filters = JSON.parse(savedFilters);
        const facoltaSelect = document.querySelector('select[name="facolta_appelli"]');
        const annoSelect = document.querySelector('select[name="anno_esame"]');
        const periodoSelect = document.querySelector('select[name="periodo_esame"]');
        const aulaSelect = document.querySelector('select[name="aula_visible"]');
        
        if (facoltaSelect && filters.facolta_appelli) facoltaSelect.value = filters.facolta_appelli;
        if (annoSelect && filters.anno_esame) annoSelect.value = filters.anno_esame;
        if (periodoSelect && filters.periodo_esame) periodoSelect.value = filters.periodo_esame;
        if (aulaSelect && filters.aula_visible) aulaSelect.value = filters.aula_visible;
        
        console.log("Filtri ripristinati:", filters);
    }
    
    // Funzione per aggiornare i link di sincronizzazione con i filtri attuali
    function updateSyncLinks() {
        const filtersJSON = sessionStorage.getItem('examoreFilters');
        if (!filtersJSON) return;
        
        const filters = JSON.parse(filtersJSON);
        
        // Costruisci la stringa di query
        let queryParams = [];
        if (filters.anno_esame) queryParams.push(`anno_esame=${filters.anno_esame}`);
        if (filters.periodo_esame) queryParams.push(`periodo_esame=${filters.periodo_esame}`);
        if (filters.facolta_appelli) queryParams.push(`facolta_id=${filters.facolta_appelli}`);
        
        const queryString = queryParams.length > 0 ? `?${queryParams.join('&')}` : '';
        
        // Aggiorna il link di sincronizzazione globale
        const syncAllLink = document.querySelector('.btn-sync-all');
        if (syncAllLink) {
            let href = syncAllLink.getAttribute('href').split('?')[0];
            syncAllLink.setAttribute('href', href + queryString);
        }
        
        // Aggiorna anche i link di sincronizzazione dei singoli appelli
        document.querySelectorAll('.sync-icon').forEach(icon => {
            let href = icon.getAttribute('href').split('?')[0];
            icon.setAttribute('href', href + queryString);
        });
        
        console.log("Link di sincronizzazione aggiornati con queryString:", queryString);
    }

    // Ripristina filtri e aggiorna link al caricamento
    restoreFilters();
    updateSyncLinks();
    
    // Funzione per ottenere il CSRF Token
    function getCSRFToken() {
        const csrfTokenElement = document.querySelector("input[name='csrfmiddlewaretoken']");
        return csrfTokenElement ? csrfTokenElement.value : null;
    }
    
    // Seleziona i form
    const filterForm = document.getElementById("filter-form");
    const auleForm = document.getElementById("aule-form");
    const dateForm = document.getElementById("dateForm");
    const todayForm = document.getElementById("today-form");

    // Funzione per gestire la richiesta AJAX
    function handleFormSubmit(event, form) {
        event.preventDefault();  // Previeni il comportamento predefinito del form

        // Ottieni i dati del form
        const formData = new FormData(form);
        
        // Salva i filtri attuali
        saveCurrentFilters();
        
        // Esegui la richiesta AJAX
        fetch(form.action, {
            method: "POST",
            body: formData,
            headers: {
                "X-Requested-With": "XMLHttpRequest",  // Identifica la richiesta come AJAX
                "X-CSRFToken": getCSRFToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            // Aggiorna i campi nella pagina con i dati ricevuti
            console.log("Data ricevuta:", data);
            updatePageContent(data);
            // Aggiorna i link di sincronizzazione dopo aver ricevuto i dati
            updateSyncLinks();
        })
        .catch(error => console.error("Errore:", error));
    }

    // Aggiungi l'evento submit ai form
    if (filterForm) {
        filterForm.addEventListener("submit", function (event) {
            handleFormSubmit(event, filterForm);
        });
    }
    if (auleForm) {
        auleForm.addEventListener("submit", function (event) {
            handleFormSubmit(event, auleForm);
        });
    }
    if (dateForm) {
        dateForm.addEventListener("submit", function(event) {
            handleFormSubmit(event, dateForm);
        });
    }
    if (todayForm) {
        todayForm.addEventListener("submit", function(event) {
            handleFormSubmit(event, todayForm);
        });
    }

    // Funzione per aggiornare il contenuto della pagina con i dati ricevuti
    function updatePageContent(data) {
        // Aggiorna gli appelli
        const eventsContainer = document.querySelector(".events");
        eventsContainer.innerHTML = "";  // Pulisci il contenitore
    
        if (data.appelli && data.appelli.length > 0) {
            data.appelli.forEach(appello => {
                const eventHTML = `
                    <div class="event">
                        <div class="title">
                            <i class="fas fa-circle"></i>
                            <h3 class="event-title">${appello.esame}</h3>
                            <a href="/sync_single_event/${appello.id}/" class="sync-icon" title="Sincronizza questo appello con Google Calendar" onclick="event.stopPropagation();">
                                <img src="/static/img/google-calendar.png" alt="Sync" style="height: 20px; margin-left: 10px;">
                            </a>
                        </div>
                        <div class="event-time">${appello.data}</div>
                    </div>`;
                eventsContainer.insertAdjacentHTML("beforeend", eventHTML);
            });
            
            // Aggiungi event listener alle icone dopo averle create
            document.querySelectorAll('.sync-icon').forEach(icon => {
                icon.addEventListener('click', function(e) {
                    e.stopPropagation();  // Ferma la propagazione dell'evento
                    // Mostra un feedback visivo immediato
                    alert("Sincronizzazione in corso...");
                });
            });
            
            // Aggiorna i link di sincronizzazione dopo aver generato il contenuto
            updateSyncLinks();
        } else {
            eventsContainer.innerHTML = `
                <div class="event">
                    <div class="title">
                        <i class="fas fa-circle"></i>
                        <h3 class="event-title">Nessun Appello Trovato</h3>
                    </div>
                </div>`;
        }
    
        // Aggiorna le disponibilità delle aule
        const leftAuleContainer = document.querySelector(".left-aule");
        const rightAuleContainer = document.querySelector(".right-aule");
        leftAuleContainer.innerHTML = "";
        rightAuleContainer.innerHTML = "";
    
        for (const [aula, disponibilita] of Object.entries(data.aule_disponibilita)) {
            leftAuleContainer.insertAdjacentHTML("beforeend", `<div class="single-aula">${aula}</div>`);
            if (disponibilita === "No disp.") {
                rightAuleContainer.insertAdjacentHTML("beforeend", `<div class="single-disp">No disp.</div>`);
            } else {
                const dispHTML = disponibilita.map(d => `<div class="single-disp">${d.ora_inizio}-${d.ora_fine}</div>`).join("");
                rightAuleContainer.insertAdjacentHTML("beforeend", `<div class="disp">${dispHTML}</div>`);
            }
        }
    
        // Aggiorna la data visualizzata
        document.getElementById("data-titolo").textContent = data.data_attuale + ":";
        document.getElementById("dta").textContent = "Disponibilità aule giorno: " + data.data_attuale;
    
        const scrapingAlertContainer = document.querySelector(".scraping-alert");
        if (data.var_disp) {
            const encodedDate = encodeURIComponent(data.data_attuale);
            scrapingAlertContainer.innerHTML = `
                <div>
                    <p class="scr-info">Non ci sono disponibilità per nessuna aula</p>
                    <a href="/scraping?data_attuale=${encodedDate}"><button class="scr-btn">Vai alla pagina per lo scraping</button></a>
                </div>`;
        } else {
            scrapingAlertContainer.innerHTML = "";
        }
    }

    // CALENDARIO:
    // Variabili per il mese e l'anno correnti
    let date = new Date();
    let currentMonth = date.getMonth();
    let currentYear = date.getFullYear();

    const months = [
        "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
        "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
    ];

    const monthEl = document.querySelector(".month .date");
    const daysEl = document.querySelector(".days");
    const prevBtn = document.querySelector(".prev");
    const nextBtn = document.querySelector(".next");
    const eventDayEl = document.querySelector(".event-day");

    function renderCalendar() {
        const firstDay = new Date(currentYear, currentMonth, 1).getDay();
        const lastDate = new Date(currentYear, currentMonth + 1, 0).getDate();
        const prevLastDate = new Date(currentYear, currentMonth, 0).getDate();

        // Impostazione del nome del mese e dell'anno
        monthEl.textContent = `${months[currentMonth]} ${currentYear}`;

        daysEl.innerHTML = "";

        // Giorni del mese precedente
        for (let x = firstDay; x > 0; x--) {
            const day = document.createElement("div");
            day.classList.add("day", "prev-date");
            day.textContent = prevLastDate - x + 1;
            daysEl.appendChild(day);
        }

        // Giorni del mese corrente
        for (let i = 1; i <= lastDate; i++) {
            const day = document.createElement("div");
            day.classList.add("day");

            if (i === date.getDate() && currentMonth === date.getMonth() && currentYear === date.getFullYear()) {
                day.classList.add("today");
            }
            day.textContent = i;

            day.addEventListener("click", () => {
                // Rimuove l'evidenziazione "today" da tutti i giorni
                document.querySelectorAll(".day").forEach(day => day.classList.remove("today"));
                // Aggiunge l'evidenziazione al giorno selezionato
                day.classList.add("today");
                
                // Cattura il giorno, mese e anno selezionati
                const selectedDate = new Date(currentYear, currentMonth, i);
                const dayValue = String(selectedDate.getDate()).padStart(2, '0');
                const monthValue = String(selectedDate.getMonth() + 1).padStart(2, '0');
                const yearValue = selectedDate.getFullYear();

                // Aggiorna il form nascosto con i valori selezionati
                document.getElementById("selectedDay").value = dayValue;
                document.getElementById("selectedMonth").value = monthValue;
                document.getElementById("selectedYear").value = yearValue;
                
                // Crea manualmente i dati del form e aggiungi i filtri
                const formData = new FormData();
                formData.append("selectedDay", dayValue);
                formData.append("selectedMonth", monthValue);
                formData.append("selectedYear", yearValue);
                
                // Aggiungi i filtri salvati al formData
                const filters = JSON.parse(sessionStorage.getItem('examoreFilters') || '{}');
                if (filters.facolta_appelli) formData.append('facolta_appelli', filters.facolta_appelli);
                if (filters.anno_esame) formData.append('anno_esame', filters.anno_esame);
                if (filters.periodo_esame) formData.append('periodo_esame', filters.periodo_esame);
                if (filters.aula_visible) formData.append('aula_visible', filters.aula_visible);

                // Ottieni il token CSRF
                const csrfToken = getCSRFToken();

                // Esegui la richiesta AJAX
                fetch(dateForm.action, {
                    method: "POST",
                    body: formData,
                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                        "X-CSRFToken": csrfToken
                    }
                })
                .then(response => response.json())
                .then(data => {
                    console.log("Data ricevuta:", data);
                    updatePageContent(data); // Aggiorna la pagina con i dati ricevuti
                })
                .catch(error => console.error("Errore:", error));
            });
            daysEl.appendChild(day);
        }

        // Giorni del mese successivo per completare la riga
        const totalDays = firstDay + lastDate;
        const nextDays = totalDays <= 35 ? 35 - totalDays : 42 - totalDays;
        for (let j = 1; j <= nextDays; j++) {
            const day = document.createElement("div");
            day.classList.add("day", "next-date");
            day.textContent = j;
            daysEl.appendChild(day);
        }
    }

    // Navigazione tra i mesi
    prevBtn.addEventListener("click", () => {
        currentMonth--;
        if (currentMonth < 0) {
            currentMonth = 11;
            currentYear--;
        }
        renderCalendar();
    });

    nextBtn.addEventListener("click", () => {
        currentMonth++;
        if (currentMonth > 11) {
            currentMonth = 0;
            currentYear++;
        }
        renderCalendar();
    });

    renderCalendar(); // Inizializzazione


    // FUNZIONAMENTO BARRA DI RICERCA:
    // Elementi della barra di ricerca
    const gotoInput = document.querySelector(".date-input");
    const gotoBtn = document.querySelector(".goto-btn");

    // Evento per il pulsante di ricerca
    gotoBtn.addEventListener("click", () => {
        const dateArr = gotoInput.value.split("/");

        // Controllo del formato GG/MM/YYYY
        if (dateArr.length === 3) {
            const day = parseInt(dateArr[0]);
            const month = parseInt(dateArr[1]) - 1;
            const year = parseInt(dateArr[2]);

            // Controllo validità del giorno, mese e anno
            if (
                day >= 1 && day <= 31 &&
                month >= 0 && month <= 11 &&
                year >= 1970 && year <= 2100
            ) {
                currentMonth = month;
                currentYear = year;
                renderCalendar();  // Aggiorna il calendario al mese e anno scelto

                // Seleziona e evidenzia il giorno specifico
                const dayElements = document.querySelectorAll(".day");
                let selectedDayFound = false;

                dayElements.forEach(dayElement => {
                    dayElement.classList.remove("today");  // Rimuove l'evidenziazione dal "today" corrente
                    if (!selectedDayFound && 
                        parseInt(dayElement.textContent) === day && 
                        !dayElement.classList.contains('prev-date') && 
                        !dayElement.classList.contains('next-date')) {
                        dayElement.classList.add("today");  // Aggiunge l'evidenziazione al giorno selezionato
                        selectedDayFound = true;
                        dayElement.click(); // Questo attiva l'evento click che carica i dati
                    }
                });
                gotoInput.value = "";
            } else {
                alert("Inserisci una data valida nel formato GG/MM/AAAA.");
            }
        } else {
            alert("Usa il formato GG/MM/AAAA.");
        }
    });

    // GESTIONE CODICE PER IL PULSANTE OGGI:
    const todayBtn = document.querySelector(".today-btn");

    todayBtn.addEventListener("click", () => {
        // Ottieni la data odierna reale
        const today = new Date();
        currentMonth = today.getMonth(); // Imposta il mese corrente
        currentYear = today.getFullYear(); // Imposta l'anno corrente

        // Aggiorna il calendario al mese e anno odierno
        renderCalendar();

        // Evidenzia il giorno attuale nel calendario
        const dayElements = document.querySelectorAll(".day");
        dayElements.forEach(dayElement => {
            dayElement.classList.remove("today"); // Rimuove l'eventuale evidenziazione "today" esistente
            if (parseInt(dayElement.textContent) === today.getDate() && 
                !dayElement.classList.contains('prev-date') && 
                !dayElement.classList.contains('next-date')) {
                dayElement.classList.add("today"); // Aggiunge l'evidenziazione al giorno attuale
                dayElement.click(); // Attiva l'evento click che carica i dati
            }
        });
    });
    
    // Aggiungi listener ai form dei filtri per salvarli quando vengono inviati
    document.querySelectorAll('#filter-form, #aule-form').forEach(form => {
        form.addEventListener('submit', function() {
            saveCurrentFilters();
            // Aggiorna i link dopo il salvataggio
            setTimeout(updateSyncLinks, 100);
        });
    });

    // Gestione pulsanti Reset filtri
    const resetAppelliBtn = document.querySelector('.reset-filter-button');
    const resetAuleBtn = document.querySelector('.reset-aule-button');

    if (resetAppelliBtn) {
        // Previeni il comportamento di default (redirect)
        resetAppelliBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Resetta i filtri degli appelli nei selettori
            const facoltaSelect = document.querySelector('select[name="facolta_appelli"]');
            const annoSelect = document.querySelector('select[name="anno_esame"]');
            const periodoSelect = document.querySelector('select[name="periodo_esame"]');
            
            if (facoltaSelect) facoltaSelect.value = '';
            if (annoSelect) annoSelect.value = '';
            if (periodoSelect) periodoSelect.value = '';
            
            // Salva i filtri aggiornati in sessionStorage
            const filters = JSON.parse(sessionStorage.getItem('examoreFilters') || '{}');
            filters.facolta_appelli = '';
            filters.anno_esame = '';
            filters.periodo_esame = '';
            sessionStorage.setItem('examoreFilters', JSON.stringify(filters));
            
            console.log("Filtri appelli resettati:", filters);
            
            // Crea una richiesta AJAX per aggiornare i dati
            const formData = new FormData();
            
            // Aggiungi i dati del giorno attualmente selezionato
            const dayValue = document.getElementById("selectedDay").value || new Date().getDate();
            const monthValue = document.getElementById("selectedMonth").value || (new Date().getMonth() + 1);
            const yearValue = document.getElementById("selectedYear").value || new Date().getFullYear();
            
            formData.append("selectedDay", dayValue);
            formData.append("selectedMonth", monthValue);
            formData.append("selectedYear", yearValue);
            
            // Aggiungi eventuali filtri aule che sono ancora attivi
            if (filters.aula_visible) formData.append('aula_visible', filters.aula_visible);
            
            // Esegui la richiesta AJAX
            fetch('/calendar/', {
                method: "POST",
                body: formData,
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    "X-CSRFToken": getCSRFToken()
                }
            })
            .then(response => response.json())
            .then(data => {
                console.log("Data ricevuta dopo reset appelli:", data);
                updatePageContent(data);
                updateSyncLinks();
            })
            .catch(error => console.error("Errore:", error));
        });
    }

    if (resetAuleBtn) {
        // Previeni il comportamento di default (redirect)
        resetAuleBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Resetta il filtro delle aule
            const aulaSelect = document.querySelector('select[name="aula_visible"]');
            if (aulaSelect) aulaSelect.value = '';
            
            // Salva i filtri aggiornati in sessionStorage
            const filters = JSON.parse(sessionStorage.getItem('examoreFilters') || '{}');
            filters.aula_visible = '';
            sessionStorage.setItem('examoreFilters', JSON.stringify(filters));
            
            console.log("Filtro aule resettato:", filters);
            
            // Crea una richiesta AJAX per aggiornare i dati
            const formData = new FormData();
            
            // Aggiungi i dati del giorno attualmente selezionato
            const dayValue = document.getElementById("selectedDay").value || new Date().getDate();
            const monthValue = document.getElementById("selectedMonth").value || (new Date().getMonth() + 1);
            const yearValue = document.getElementById("selectedYear").value || new Date().getFullYear();
            
            formData.append("selectedDay", dayValue);
            formData.append("selectedMonth", monthValue);
            formData.append("selectedYear", yearValue);
            
            // Aggiungi eventuali filtri appelli che sono ancora attivi
            if (filters.facolta_appelli) formData.append('facolta_appelli', filters.facolta_appelli);
            if (filters.anno_esame) formData.append('anno_esame', filters.anno_esame);
            if (filters.periodo_esame) formData.append('periodo_esame', filters.periodo_esame);
            
            // Esegui la richiesta AJAX
            fetch('/calendar/', {
                method: "POST",
                body: formData,
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    "X-CSRFToken": getCSRFToken()
                }
            })
            .then(response => response.json())
            .then(data => {
                console.log("Data ricevuta dopo reset aule:", data);
                updatePageContent(data);
                updateSyncLinks();
            })
            .catch(error => console.error("Errore:", error));
        });
    }
});