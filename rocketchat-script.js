class Script {
  process_incoming_request({ request }) {
    const build = request.content.build;
    if (build.status === 'success') return this.success(build);
    if (build.status === 'failure') return this.failure(build);
    if (build.status === 'initiated') return this.initiated(build);
    return this.other(build);
  }
  initiated(build) {
   	return this.respond(build, '#66A9CC', 'build started'); 
  }
  success(build) {
    return this.respond(build, '#4BB543', 'build succeeded');
  }
  failure(build) {
    return this.respond(build, '#CC0000', 'build failed');
  }
  other(build) {
   	return this.respond(build, '#7F7F7F', `build ${build.status}`);
  }
  respond({ committer, message, branch, commit_url, build_url, project_name }, color, title) {
    return {
      content: {
        text: `see commit: [${branch}](${commit_url})\nsee [build log](${build_url})`,
        attachments: [{
          title: `${project_name}: ${title}`,
          color: color,
          text: `${committer}: ${message}`,
        }],
      },
    };
  }
}
