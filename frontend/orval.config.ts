export default {
  api: {
    input: {
      target: '../backend/openapi.json',
    },
    output: {
      target: './src/shared/api/generated/',
      client: 'fetch',
      httpClient: 'fetch',
      mutator: {
        path: './src/shared/api/mutator.ts',
        name: 'customInstance',
      },
      clean: true,
      prettier: true,
    },
  },
}
