invisible [
    invisible(render=includeCS, data={'hdf':vars.hdf, 'template':"header.cs"}),
    slot('pagebody'),
    invisible(render=includeCS, data={'hdf':vars.hdf, 'template':"footer.cs"}),
]
