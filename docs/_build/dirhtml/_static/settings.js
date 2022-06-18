'use-strict';

let settingsModal;

class Setting {
  constructor(name, defaultValue, setter) {
    this.name = name;
    this.defaultValue = defaultValue;
    this.setValue = setter;
  }

  setElement() {
    throw new TypeError('Abstract methods should be implemented.');
  }

  load() {
    let value = JSON.parse(localStorage.getItem(this.name));
    this.value = value === null ? this.defaultValue : value;
    try {
      this.setValue(this.value);
    } catch (error) {
      console.error(`Failed to apply setting "${this.name}" With value:`, this.value);
      console.error(error);
    }
  }

  update() {
    throw new TypeError('Abstract methods should be implemented.');
  }

}

class CheckboxSetting extends Setting {

  setElement() {
    let element = document.querySelector(`input[name=${this.name}]`);
    element.checked = this.value;
  }

  update(element) {
    localStorage.setItem(this.name, element.checked);
    this.setValue(element.checked);
  }

}

class RadioSetting extends Setting {

  setElement() {
    let element = document.querySelector(`input[name=${this.name}][value=${this.value}]`);
    element.checked = true;
  }

  update(element) {
    localStorage.setItem(this.name, `"${element.value}"`);
    this.setValue(element.value);
  }

}

function getRootAttributeToggle(attributeName, valueName) {
  function toggleRootAttribute(set) {
    if (set) {
      document.documentElement.setAttribute(`data-${attributeName}`, valueName);
    } else {
      document.documentElement.removeAttribute(`data-${attributeName}`);
    }
  }
  return toggleRootAttribute;
}

function setTheme(value) {
  if (value === 'automatic') {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      document.documentElement.setAttribute('data-theme', 'dark');
    } else {
      document.documentElement.setAttribute('data-theme', 'light');
    }
  }
  else {
    document.documentElement.setAttribute('data-theme', value);
  }
}

const settings = [
  new CheckboxSetting('useSerifFont', false, getRootAttributeToggle('font', 'serif')),
  new RadioSetting('setTheme', 'automatic', setTheme)
]

function updateSetting(element) {
  let setting = settings.find((s) => s.name == element.name);
  if (setting) {
    setting.update(element);
  }
}

for (const setting of settings) {
  setting.load();
}

function sleep(s) {
  return new Promise(resolve => setTimeout(resolve, s * 1000));
}

let gearwheel

async function openModal(event, close) {
  gearwheel.classList.remove("fa-shake");
  gearwheel.style = `${!close ? "--fa-animation-direction: reverse; " : ""}--fa-animation-duration: 1s;`;
  gearwheel.classList.add("fa-spin");
  
  sleep(0.5)
    .then(() => (!close ? settingsModal.open() : settingsModal.close()))
    .then(() => gearwheel.classList.remove("fa-spin"))
    .then(() => gearwheel.style = `--fa-animation-duration: 1s;`)
}

document.addEventListener('DOMContentLoaded', () => {
  gearwheel = document.getElementsByClassName("fa-gear")[0];
  settingsModal = new Modal(document.querySelector('div#settings.modal'));
  for (const setting of settings) {
    setting.setElement();
  }
  gearwheel.addEventListener(
    'mouseover',
    (event) => {
      gearwheel.style = "--fa-animation-direction: reverse; --fa-animation-duration: 3s;";
      gearwheel.classList.add("fa-shake");
    });
  gearwheel.addEventListener(
    'mouseout',
    (event) => {
      //event.target.style = "--fa-animation-duration: 20s;";
      gearwheel.classList.remove("fa-shake");
    });
  gearwheel.addEventListener('click', openModal)
});