# ~/clientfactory/src/clientfactory/backends/algolia.py
"""
Algolia Backend Implementation
-----------------------------
Backend for Algolia search API with index management and parameter handling.
"""
from __future__ import annotations
import typing as t, urllib.parse

from pydantic import field_validator as fieldvalidator
from schematix import Field, Schema

from clientfactory.core.bases import BaseBackend
from clientfactory.core.models import BackendConfig, RequestModel, ResponseModel


class AlgoliaConfig(BackendConfig):
    """Configuration for Algolia backend."""
    appid: str = ""
    apikey: str = ""
    index: str = ""
    indices: t.List[str] = []
    agent: str = "ClientFactory"
    urlbase: str = "https://{appid}-dsn.algolia.net"
    contenttype: str = 'application/json'  # Configurable content type
    encodeparams: bool = False  # Whether to URL encode params
    mergeresults: bool = False  # Whether to merge multi-index results

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
    facets = Field(source="facets", target="facets", default=[])
    attributesToRetrieve = Field(source="attributesToRetrieve", target="attributesToRetrieve", default=["*"])
    attributesToHighlight = Field(source="attributesToHighlight", target="attributesToHighlight", default=[])


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
    __declattrs__: set[str] = BaseBackend.__declattrs__ | {'appid', 'apikey', 'index', 'indices', 'facetsmap', 'numerics'}
    __declconfs__: set[str] = BaseBackend.__declconfs__ | {'urlbase', 'agent', 'indices', 'index', 'appid', 'apikey', 'content'}

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
            facetname = mapping.get(k, k)

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

    def _buildstandardparams(self, data: dict) -> dict:
        """
        Build common Algolia parameters from data.

        Args:
            data: Input data dictionary

        Returns:
            Dict of standard Algolia parameters
        """
        #! todo: convert to Schema
        params = {}
        standard = {
            'analytics',
            'click_analytics',
            'enable_ab_test',
            'highlight_pre_tag',
            'highlight_post_tag',
            'facets',
            'max_values_per_facet',
            'get_ranking_info',
            'attributes_to_retrieve',
            'attributes_to_highlight',
        }
        camelize = lambda s: s if ('_' not in s) else (s.split('_')[0] + ''.join(w.title() for w in s.split('_')[1:]))
        for key in standard:
            camel = camelize(key)
            if (key in data):
                params[camel] = data[key]
            elif (camel in data):
                params[camel] = data[camel]
        return params

    def _convertparams(self, data: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
        """Convert search parameters to Algolia format."""
        params = self._paramschema.transform(data)

        if ('offset' in data) and ('limit' in data):
            params['page'] = int(data['offset']) // int(data['limit'])

        return params

    def _formatrequest(self, request: RequestModel, data: t.Dict[str, t.Any]) -> RequestModel:
        """Format request for Algolia API."""
        if not data:
            return request

        baseurl = self._config.baseurl

        # Get indices - either from data, config.indices, or fallback to single index
        indices = data.pop('indices', self._config.indices or [self.index])
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

        # add standard parameters
        standardparams = self._buildstandardparams(data)
        parameters.update(standardparams)


        # encode if configured
        if self._config.encodeparams:
            params = urllib.parse.urlencode(parameters)
        else:
            params = parameters

        # build requests array for multi-index support
        requests = [
            {
                "indexName": index,
                "params": params
            }
            for index in indices
        ]

        payload = {"requests": requests}
        agent = urllib.parse.urlencode({'x-algolia-agent': self._config.agent})
        url = f"{baseurl}/1/indexes/*/queries?{agent}"

        update = {
            'url': url,
            'json': payload,
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
        if not response.ok:
            return response

        try:
            data = response.json()
            print(f"DEBUG Algolia: data = {data}")
            print(f"DEBUG Algolia: raiseonerror = {self._config.raiseonerror}")

            # Check for Algolia-specific errors like CFv2
            if ("message" in data) and ("status" in data) and (int(data["status"]) >= 400):
                print(f"DEBUG Algolia: Found error, should raise = {self._config.raiseonerror}")
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
