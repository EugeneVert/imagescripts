#compdef imagescripts.py

_arguments -C \
    '1:module:->modules' \
    '2:submodule:->submodules'

case "$state" in
    (modules)
        _values 'modules' \
            'size' \
            'find' \
            'generate'
        ;;
    (submodules)
        case "${words[2]}" in
            (find)
                _values 'find' \
                    'resizable' \
                    'samesize' \
                    'simmilar'
                ;;
            (generate)
                _values 'generate' \
                    'video' \
                    'fromjson'
        esac
        ;;
esac
