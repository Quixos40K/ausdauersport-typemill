<?php

namespace Plugins\jsonldmeta;

use Typemill\Plugin;

/**
 * Adds an editable JSON-LD field to Typemill's Meta tab and renders valid
 * JSON-LD in the frontend through assets.renderMeta().
 */
class jsonldmeta extends Plugin
{
    public static function getSubscribedEvents()
    {
        return [
            'onMetaLoaded' => ['onMetaLoaded', 0],
        ];
    }
