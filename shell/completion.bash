#!/usr/bin/env bash

_imagescripts.py(){
    local cur prev words cword
    _init_completion
    if ((cword == 1)); then
        COMPREPLY=($(compgen -W 'size find generate' -- "$cur"))
        return
    fi
    case $prev in
        "find")
            COMPREPLY=($(compgen -W 'resizable samesize simmilar' -- "$cur"))
            return
            ;;
        "generate")
            COMPREPLY=($(compgen -W 'video fromjson' -- "$cur"))
            return
            ;;
    esac
}

complete -F _imagescripts.py imagescripts.py
