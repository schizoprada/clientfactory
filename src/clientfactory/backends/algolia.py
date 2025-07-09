# ~/clientfactory/src/clientfactory/backends/algolia.py
"""
Algolia Backend Implementation
-----------------------------
Backend for Algolia search API with index management and parameter handling.
"""
from __future__ import annotations
import typing as t, urllib.parse, json as _json

from pydantic import field_validator as fieldvalidator
from schematix import Field, Schema

from clientfactory.core.bases import BaseBackend
from clientfactory.core.models import BackendConfig, RequestModel, ResponseModel

from clientfactory.logs import log

class AlgoliaConfig(BackendConfig):
    """Configuration for Algolia backend."""
    appid: str = ""
    apikey: str = ""
    index: str = ""
    indices: t.List[str] = []
    agent: str = "ClientFactory"
    encodeagent: bool = False # new
    urlbase: str = "https://{appid}-dsn.algolia.net"
    contenttype: str = 'application/json'  # Configurable content type
    encodeparams: bool = True  # Whether to URL encode params
    paramdelimiter: str = '&'
    postprocess: bool = False
    mergeresults: bool = False  # Whether to merge multi-index results
    multirequest: bool = True # build multi-request array



    @fieldvalidator('urlbase')
    @classmethod
    def _validateurlbase(cls, v: str) -> str:
        """Ensure urlbase matches Algolia structure"""
        if v is None:
            raise ValueError(f"Algolia urlbase is required")
        if '{appid}' not in v: #! revise
            raise ValueError("Algolia urlbase must contain '{appid}'")
        return v

    @property
    def baseurl(self) -> str:
        """Get the formatted base URL with app ID."""
        if "{appid}" in self.urlbase:
            return self.urlbase.format(appid=self.appid)
        return self.baseurl


class AlgoliaParams(Schema):
    query = Field(source="q", target="query") | Field(source="query", target="query")
    hitsPerPage = Field(source="limit", target="hitsPerPage") | Field(source="hitsPerPage", target="hitsPerPage")
    page = Field(source="page", target="page", default=0)
    filters = Field(source="filters", target="filters", default="")
    facets = Field(source="facets", target="facets", default=["badges", "location", "price_i", "strata"])
    #attributesToRetrieve = Field(source="attributesToRetrieve", target="attributesToRetrieve", default=["*"])
    #attributesToHighlight = Field(source="attributesToHighlight", target="attributesToHighlight", default=[])
    analytics = Field(source="analytics", target="analytics")
    clickAnalytics = Field(source="clickAnalytics", target="clickAnalytics")
    enableABTest = Field(source="enableABTest", target="enableABTest")
    getRankingInfo = Field(source="getRankingInfo", target="getRankingInfo")
    highlightPreTag = Field(source="highlightPreTag", target="highlightPreTag")
    highlightPostTag = Field(source="highlightPostTag", target="highlightPostTag")
    maxValuesPerFacet = Field(source="maxValuesPerFacet", target="maxValuesPerFacet")

class AlgoliaResponse(Schema):
    hits = Field(source="hits", target="hits")
    total = Field(source="nbHits", target="total")
    page = Field(source="page", target="page")
    pages = Field(source="nbPages", target="pages")
    hitsPerPage = Field(source="hitsPerPage", target="hitsPerPage")
    processingTime = Field(source="processingTimeMS", target="processingTime")
    query = Field(source="query", target="query")
    facets = Field(source="facets", target="facets", default={})
    facets_stats = Field(source="facets_stats", target="facets_stats", default={})



class AlgoliaBackend(BaseBackend):
    """
    Algolia search backend implementation.

    Handles Algolia's specific API format, authentication, and response processing.
    """
    __declaredas__: str = 'algolia'
    __declattrs__: set[str] = BaseBackend.__declattrs__ | {'appid', 'apikey', 'index', 'indices', 'facetsmap', 'numerics', 'facets'}
    __declconfs__: set[str] = BaseBackend.__declconfs__ | {
        'urlbase', 'agent', 'indices', 'index', 'appid', 'apikey',
        'contenttype', 'encodeparams', 'paramdelimiter', 'encodeagent',
        'multirequest', 'postprocess'
    }

    def __init__(
        self,
        config: t.Optional[AlgoliaConfig] = None,
        **kwargs: t.Any
    ) -> None:
        # 1. resolve components
        components = self._resolvecomponents() # not needed

        # 2. resolve config
        self._config: AlgoliaConfig = self._resolveconfig(AlgoliaConfig, config, **kwargs) #type: ignore

        # 3. resolve attributes
        attrs = self._collectattributes(**kwargs)
        self._resolveattributes(attrs)
        self._paramschema: Schema = AlgoliaParams()
        self._responseschema: Schema = AlgoliaResponse()

    def _resolveattributes(self, attributes: dict) -> None:
        super()._resolveattributes(attributes)
        self.appid: str = attributes.get('appid', '')
        self.apikey: str = attributes.get('apikey', '')
        self.index: str = attributes.get('index', '')
        self.facetsmap: dict = attributes.get('facetsmap', {})
        self.numerics: list = attributes.get('numerics', [])
        self.facets: set = set(attributes.get('facets', []) or [])


    def _buildfacetfilters(self, data: dict, facetsmap: t.Optional[dict] = None) -> list:
        """Build standard Algolia facet filters from data.

        Args:
            data: Input data dictionary
            facetmapping: Optional mapping of data keys to Algolia facet names
                         e.g. {"designers": "designers.name", "department": "department"}

        Returns:
            List of facet filters in Algolia format: [["facet:value"], ["facet2:value2"]]
        """
        filters = []
        mapping = (facetsmap or self.facetsmap or {})

        for k,v in data.items():
            if (v is None) or (v == ""):
                continue

            # Get the facet name (use mapping if provided, otherwise use key as-is)
            if k in (self.facets or set()):
                facetname = k
            elif k in mapping:
               facetname = mapping[k]
            else:
               continue # not a facet field

            if isinstance(v, list):
                # Multiple values for same facet (OR logic within the group)
                if v:
                    # Only add if list is not empty
                    group = [f"{facetname}:{val}" for val in v if val is not None]
                    if group:
                        filters.append(group)
            else:
                filters.append([f"{facetname}:{v}"])

        return filters

    def _buildnumericfilters(self, data: dict, numeric: t.Optional[list] = None) -> list:
        """"""
        filters = []
        numerics = (numeric or self.numerics or [])

        for field in numerics:
            minkey = f"{field}_min"
            maxkey = f"{field}_max"

            if (minkey in data) and (data[minkey] is not None):
                filters.append(f"{field}>={data[minkey]}")

            if (maxkey in data) and (data[maxkey] is not None):
                filters.append(f"{field}<={data[maxkey]}")

            # check for direct field acces with operators
            if (field in data) and (data[field] is not None):
                value = data[field]
                if isinstance(value, dict):
                    if ("min" in value) and (value["min"] is not None):
                        filters.append(f"{field}>={data["min"]}")
                    if ("max" in value) and (value["max"] is not None):
                        filters.append(f"{field}<={data["max"]}")
                elif isinstance(value, (int, float)):
                    filters.append(f"{field}={value}")

        return filters

    def _convertparams(self, data: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
        """Convert search parameters to Algolia format."""
        params = self._paramschema.transform(data)

        if ('offset' in data) and ('limit' in data):
            params['page'] = int(data['offset']) // int(data['limit'])

        params['facets'] = list(set(params.get('facets', []) + list(self.facets)))

        return {k:v for k,v in params.items() if v is not None}

    def _urlencode(self, parameters: dict) -> str:
        """URL encode parameters with configurable delimiter."""
        def serialize(v: t.Any) -> str:
            import json
            if isinstance(v, bool):
                return str(v).lower()
            elif isinstance(v, (list, dict)):
                return json.dumps(v)
            else:
                return str(v)

        if self._config.paramdelimiter == '&':
            serialized = {k: serialize(v) for k, v in parameters.items()}
            return urllib.parse.urlencode(serialized)

        encode = lambda v: urllib.parse.quote_plus(serialize(v))
        pair = lambda k, v: f"{k}={v}"
        encoded = [
            pair(encode(k), encode(v))
            for k,v in parameters.items()
        ]
        return self._config.paramdelimiter.join(encoded)

    def _buildrequestarray(self, indices: list, parameters: dict) -> list:
        """
        Build array of Algolia search requests for multi-facet querying.

        Creates the standard Algolia multi-request pattern used by search UIs:
        1. Main request with all filters applied to get actual search results
        2. Additional requests excluding each filtered facet to get facet counts
        3. Special request for price_i facet (if present) to get price distribution

        This matches the behavior of Algolia's InstantSearch widgets which need
        facet counts to show available filter options in the UI.

        Args:
            indices: List of Algolia index names to search
            parameters: Search parameters including facetFilters, facets, etc.

        Returns:
            List of request objects for Algolia's multi-index search endpoint

        Example:
            With facetFilters=[["brand:Nike"], ["category:shoes"]] and
            facets=["brand", "category", "price_i"], creates 4 requests:
            - Main search with both filters
            - Search excluding brand filter (for brand facet counts)
            - Search excluding category filter (for category facet counts)
            - Search with all filters for price_i facet counts
        """
        requests = []

        # encode if configured
        if self._config.encodeparams: params = self._urlencode(parameters)
        else: params = parameters

        facetfilters = parameters.get('facetFilters', [])
        facets = parameters.get('facets', [])

        for index in indices:

            # Request 1: Full search with all filters - this gives actual results
            requests.append({
                "indexName": index,
                "params": params
            })

            # Requests 2-N: Remove each facet group for UI facet counts
            if (facetfilters and self._config.multirequest and facets):

                filteredfacets = set()
                for filtergroup in facetfilters:
                    for filteritem in filtergroup:
                        facetname = filteritem.split(':')[0]
                        filteredfacets.add(facetname)


                for facet in facets:
                    if facet in filteredfacets:
                        modparams = parameters.copy()
                        remainingfilters = []

                        for filtergroup in facetfilters:
                            groupremaining = [f for f in filtergroup if not f.startswith(f"{facet}:")]
                            if groupremaining:
                                remainingfilters.append(groupremaining)

                        if remainingfilters:
                            modparams['facetFilters'] = remainingfilters
                        else:
                            modparams.pop('facetFilters', None)

                        # Set single facet for this request
                        modparams['facets'] = [facet]
                        modparams['hitsPerPage'] = 0
                        modparams['analytics'] = False
                        modparams['clickAnalytics'] = False


                        if self._config.encodeparams:
                            modparams = self._urlencode(modparams)


                        requests.append({
                            "indexName": index,
                            "params": modparams
                        })

                # special case for price_i
                if ('price_i' in facets) and ('price_i' not in filteredfacets):
                    modparams = parameters.copy()
                    modparams['facets'] = ['price_i']
                    modparams['hitsPerPage'] = 0
                    modparams['analytics'] = False
                    modparams['clickAnalytics'] = False

                    if self._config.encodeparams:
                        modparams = self._urlencode(modparams)

                    requests.append({
                        "indexName": index,
                        "params": modparams
                    })

        return requests

    def _getindices(self, data: dict) -> list:
        """..."""
        log.info(f"DEBUG _getindices -- data: {data}")
        if 'index' in data:
            return [data.pop('index')]
        elif 'indices' in data:
            return data.pop('indices', [])
        else:
            return (self._config.indices or [self.index])

    def _formatrequest(self, request: RequestModel, data: t.Dict[str, t.Any]) -> RequestModel:
        """Format request for Algolia API."""

        if not data:
            return request

        baseurl = self._config.baseurl

        # Get indices - either from data, config.indices, or fallback to single index
        indices = self._getindices(data)
        if (not indices) or (not any(indices)):
            raise ValueError("At least one index is required for Algolia search")

        parameters = self._convertparams(data)
        # add facet filters
        facetfilters = self._buildfacetfilters(data)
        if facetfilters:
            parameters['facetFilters'] = facetfilters

        # add numeric filters
        numericfilters = self._buildnumericfilters(data)
        if numericfilters:
            parameters['numericFilters'] = numericfilters

        # build requests array for multi-index support
        requests = self._buildrequestarray(indices, parameters)
        payload = {"requests": requests}
        agent = f"x-algolia-agent={urllib.parse.quote(urllib.parse.unquote(self._config.agent)) if self._config.encodeagent else self._config.agent}"
        url = f"{baseurl}/1/indexes/*/queries?{agent}"



        update = {
            'url': url,
            'json': None,
            'data': _json.dumps(payload),
            'headers': {
                **request.headers,
                'X-Algolia-Application-Id': self.appid,
                'X-Algolia-API-Key': self.apikey,
                'Content-Type': self._config.contenttype
            }
        }

        return request.model_copy(update=update)

    def _mergeresults(self, results: list[dict], indices: list[str]) -> dict:
        """Merge multi-index Algolia response"""
        processed = [self._responseschema.transform(result) for result in results]

        # Tag hits with source index and collect all hits
        allhits = []
        for i, result in enumerate(processed):
            for hit in result.get('hits', []):
                hit['_index'] = indices[i]
                allhits.append(hit)

        # Use first result as base and override with aggregated data
        merged = processed[0].copy() if processed else {}
        merged.update({
            'hits': allhits,
            'total': sum(r.get('total', 0) for r in processed),
            'processingTime': sum(r.get('processingTime', 0) for r in processed),
            'indices': indices
        })

        # Merge facets
        for result in processed[1:]:
            merged['facets'].update(result.get('facets', {}))
            merged['facets_stats'].update(result.get('facets_stats', {}))

        return merged

    def _processresponse(self, response: ResponseModel) -> t.Any:
        """Process Algolia response with CFv2-style error handling."""
        if not response.ok or not self._config.postprocess:
            return response

        try:
            data = response.json()

            # Check for Algolia-specific errors like CFv2
            if ("message" in data) and ("status" in data) and (int(data["status"]) >= 400):
                if self._config.raiseonerror:
                    raise RuntimeError(f"Algolia Error: {data['message']}")

            # Return results array for multi-index or single result
            results = data.get('results', [data])

            if self._config.mergeresults and len(results) > 1:
                return self._mergeresults

            result = results[0] if results else {} #! TODO: process all results
            return self._responseschema.transform(result)
        except ValueError as e:
            import warnings
            warnings.warn(f"Exception parsing JSON response, returning as text: {e}")
            return response.text
