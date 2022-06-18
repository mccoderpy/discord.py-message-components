from typing import Dict, Any

from discord import Localizations

DATA: Dict[str, Dict[str, Any]] = {
    'slash_command_responses': {
        'poll_create': {
            'setups': {
                'reason_modal': {
                    'title': Localizations(
                        english_GB='Add a new reason field',
                        german='Füge ein neues Begründungsfeld hinzu'
                    ),
                    'fields': {
                        'label': {
                            'label': Localizations(
                                english_GB='The label of the field.',
                                german='Die Überschrift des Feldes.'
                            ),
                            'value': Localizations(
                                english_GB='Why did you chose {{option}}?',
                                german='Warum hast du {{option}} gewählt?'
                            ),
                            'placeholder': Localizations(
                                english_GB='Provide a label for the field | {{option}} will be replaced with the selected option/s',
                                german='Gebe eine Überschrift für das Feld an | {{option}} wird mit der/n ausgewählte/n Option/en ersetzt'
                            )
                        },
                        'value': {
                            'label': Localizations(
                                english_GB='The default value of the field.',
                                german='Der standardgemäße Inhalt des Feldes.'
                            ),
                            'value': Localizations(
                                english_GB=None,
                                german=None
                            ),
                            'placeholder': Localizations(
                                english_GB='Provide a default value for the field | {{option}} will be replaced with the selected option/s',
                                german='Gebe den standardgemäßen Inhalt an | {{option}} wird mit der/n ausgewählte/n Option/en ersetzt'
                            )
                        },
                        'placeholder': {
                            'label': Localizations(
                                english_GB='The placeholder of the field.',
                                german='Der Platzhalter des Feldes.'
                            ),
                            'value': Localizations(
                                english_GB='Provide an option.',
                                german='Gebe einen wert an.'
                            ),
                            'placeholder': Localizations(
                                english_GB='Provide a placeholder for the field | {{option}} will be replaced with the selected option/s',
                                german='Gebe einen Platzhalter für das Feld an | {{option}} wird mit der/n ausgewählte/n Option/en ersetzt'
                            )
                        }
                    }
                }
            }
        }
    },
    'button_responses': {
        'poll_create': {
            'add_option': {
                'option_name_already_taken': {
                    'title': Localizations(
                        english_GB='A option with this name already exists',
                        german='Eine Option mit diesem Namen existiert bereits'
                    ),
                    'description': Localizations(
                        english_GB='An option with the name `{name}` is already present, try using another name instead.',
                        german='Eine Option mit dem Namen `{name}` ist bereits vorhanden. Versuche einen anderen Namen zu nutzen.',
                    ),
                    'description_field': {
                        'name': Localizations(
                            english_GB='Here is the description, if you need it again.',
                            german='Hier ist die Beschreibung, falls du sie noch mal brauchst'
                        )
                    }
                },
                'choose_option_placeholder': Localizations(
                    english_GB='Choose up to {max_choices} from {choices} options{min_choices}',
                    german='Wähle bis zu {max_choices} aus {choices} Optionen{min_choices}'
                ),
                'select menu': {
                    'title': Localizations(english_GB='Add a new option', german='Füge eine neue Option hinzu'),
                    'fields': {
                        'name': {
                            'label': Localizations(
                                english_GB='What should be the options name?',
                                german='Was soll der Name der Option sein?'
                            ),
                            'placeholder': Localizations(
                                english_GB='The name of the option',
                                german='Der Name der Option'
                            )
                        },
                        'description': {
                            'label': Localizations(
                                english_GB='Description',
                                german='Beschreibung'
                            ),
                            'placeholder': Localizations(
                                english_GB='Describe the option',
                                german='Beschreibe die Option'
                            )
                        }
                    }
                },
                'button': {

                },
                'reaction': {

                }
            }
        }
    }
}
