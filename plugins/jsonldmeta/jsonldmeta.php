<?php

namespace Plugins\jsonldmeta;

use Typemill\Plugin;

/**
 * Adds a JSON-LD code field to Typemill's existing Meta tab.
 *
 * The field itself is declared in jsonldmeta.yaml. Typemill stores the
 * entered value in the page-specific YAML file as meta.json_ld.
 */
class jsonldmeta extends Plugin
{
    public static function getSubscribedEvents(): array
    {
        return [];
    }
}
